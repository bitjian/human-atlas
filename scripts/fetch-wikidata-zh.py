"""从 Wikidata 按 FMA 编号批量拉取中文标签，用权威译名校验/补全术语表。

Wikidata 的 P1402 属性正是 Foundational Model of Anatomy 编号，与本项目的
concept.id / part.conceptId 完全对应，因此可以直接批量反查中文名。

数据许可：Wikidata 为 CC0（公有领域），可自由使用于本项目。

用法：
  python3 scripts/fetch-wikidata-zh.py            # 拉取并写入 app/i18n/wikidata-zh.json
  python3 scripts/fetch-wikidata-zh.py --dry      # 只统计能命中多少，不写文件

拉取完成后，重新运行 scripts/translate-anatomy-zh.py 即可让权威译名生效
（优先级：手写词条 > Wikidata 译名 > 规则生成）。
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = os.path.join(ROOT, 'public/models/atlas.json')
OUT = os.path.join(ROOT, 'app/i18n/wikidata-zh.json')

SPARQL = 'https://query.wikidata.org/sparql'
UA = 'human-atlas-i18n/1.0 (localization script)'
BATCH = 150          # 每批查询的 FMA 编号数
TIMEOUT = 60         # 单次请求超时（秒）
RETRY = 2            # 失败重试次数
PAUSE = 1.0          # 批次间隔，避免给公共端点压力


def build_query(fma_ids):
    values = ' '.join('"%s"' % f for f in fma_ids)
    return f"""SELECT ?fma ?label WHERE {{
  VALUES ?fma {{ {values} }}
  ?item wdt:P1402 ?fma.
  ?item rdfs:label ?label.
  FILTER(LANGMATCHES(LANG(?label), "zh"))
}}"""


def run_batch(fma_ids):
    for attempt in range(RETRY + 1):
        try:
            data = urllib.parse.urlencode({
                'query': build_query(fma_ids),
                'format': 'json',
            }).encode()
            req = urllib.request.Request(SPARQL, data=data, headers={
                'User-Agent': UA,
                'Accept': 'application/sparql-results+json',
                'Content-Type': 'application/x-www-form-urlencoded',
            })
            payload = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
            hits = {}
            for row in payload['results']['bindings']:
                fma = row['fma']['value']
                label = row['label']['value']
                # 同一实体可能有多个中文变体，取第一个即可
                hits.setdefault(fma, label)
            return hits, None
        except Exception as exc:  # noqa: BLE001 网络错误种类繁多，统一重试
            if attempt == RETRY:
                return {}, f'{type(exc).__name__}: {exc}'
            time.sleep(PAUSE * (attempt + 1))
    return {}, 'unreachable'


def main():
    dry = '--dry' in sys.argv
    atlas = json.load(open(ATLAS))
    fma_ids = sorted({c['id'] for c in atlas['concepts']} | {p['conceptId'] for p in atlas['parts']})
    print('待查询 FMA 编号：%d 个' % len(fma_ids))

    result, failures = {}, 0
    for i in range(0, len(fma_ids), BATCH):
        batch = fma_ids[i:i + BATCH]
        hits, err = run_batch(batch)
        if err:
            failures += 1
            print('  批次 %d 失败：%s' % (i // BATCH + 1, err))
            if failures >= 3:
                print('\n连续失败，可能是网络不可达或端点限流。稍后重试即可。')
                break
            continue
        result.update(hits)
        print('  批次 %d/%d：命中 %d 条（累计 %d）'
              % (i // BATCH + 1, (len(fma_ids) + BATCH - 1) // BATCH, len(hits), len(result)))
        time.sleep(PAUSE)

    print('\n共获得中文标签 %d 条，覆盖率 %.0f%%' % (len(result), len(result) / len(fma_ids) * 100))

    if dry or not result:
        print('（--dry 模式，未写入文件）' if dry else '（无结果，未写入文件）')
        return

    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=0, sort_keys=True)
    print('已写入 %s' % OUT)
    print('下一步：重新运行 scripts/translate-anatomy-zh.py 让权威译名生效。')


if __name__ == '__main__':
    main()
