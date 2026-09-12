"""从 Wikidata 按 FMA 编号批量拉取中文标签，用权威译名校验/补全术语表。

Wikidata 的 P1402 属性正是 Foundational Model of Anatomy 编号，与本项目的
concept.id / part.conceptId 完全对应，因此可以直接批量反查中文名。

数据许可：Wikidata 为 CC0（公有领域），可自由使用于本项目。

⚠ 两个已修复的坑（2026-09-12）：
  1. P1402 的字面量是【裸数字】（如 "7203"），不是 "FMA7203" 带前缀形式。
     原实现直接用 concept.id 拼 VALUES，导致 0 命中。
  2. query.wikidata.org 在部分网络环境下不可达（TLS 握手超时），
     已加入 OpenLink 公共镜像作为回退端点。

用法：
  python3 scripts/fetch-wikidata-zh.py            # 拉取并写入 app/i18n/wikidata-zh.json
  python3 scripts/fetch-wikidata-zh.py --dry      # 只统计能命中多少，不写文件

依赖：zhconv（推荐）。Wikidata 上约 43% 的中文标签只有繁体变体，
      装上 zhconv 可把它们统一转成简体，命中率更高；
      未安装时脚本降级为「只采纳简体变体」，不会把繁体写进术语表。

拉取完成后，重新运行 scripts/translate-anatomy-zh.py 即可让权威译名生效
（优先级：手写词条 > Wikidata 译名 > 规则生成）。
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

try:                       # 简繁归一：Wikidata 有大量仅存繁体变体的条目
    from zhconv import convert as _to_simplified
except ImportError:        # 缺失时降级（保留原标签，但会污染简体术语表）
    _to_simplified = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = os.path.join(ROOT, 'public/models/atlas.json')
OUT = os.path.join(ROOT, 'app/i18n/wikidata-zh.json')

# 主端点优先，不可达时自动回退到镜像（内容同为 Wikidata 快照）
ENDPOINTS = [
    'https://query.wikidata.org/sparql',
    'https://wikidata.demo.openlinksw.com/sparql',
]
UA = ('HumanAtlas-i18n/1.0 (anatomy term localization; '
      'contact: zizi-abitjian@wechat)')
BATCH = 400          # 每批查询的 FMA 编号数（POST，避免 GET 414）
TIMEOUT = 60         # 单次请求超时（秒）
RETRY = 2            # 每个端点的失败重试次数
PAUSE = 0.5          # 批次间隔，避免给公共端点压力

# 中文标签变体优先级：大陆简体优先
LANG_RANK = {'zh-hans': 0, 'zh-cn': 1, 'zh': 2, 'zh-sg': 3, 'zh-my': 4,
             'zh-hant': 8, 'zh-tw': 9, 'zh-hk': 10, 'zh-mo': 11}
# 明确的简体变体（无 zhconv 时的降级白名单，避免把繁体写进简体术语表）
SIMPLIFIED_LANGS = {'zh-hans', 'zh-cn', 'zh-sg', 'zh-my'}


def build_query(fma_ids):
    """fma_ids 为带前缀的 'FMA7203' 形式；P1402 字面量需去掉前缀。"""
    values = ' '.join('"%s"' % (f[3:] if f.upper().startswith('FMA') else f)
                      for f in fma_ids)
    return f"""SELECT ?fma ?label WHERE {{
  VALUES ?fma {{ {values} }}
  ?item wdt:P1402 ?fma.
  ?item rdfs:label ?label.
  FILTER(LANGMATCHES(LANG(?label), "zh"))
}}"""


def _post(endpoint, query, timeout=TIMEOUT):
    data = urllib.parse.urlencode({'query': query, 'format': 'json'}).encode()
    req = urllib.request.Request(endpoint, data=data, headers={
        'User-Agent': UA,
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/x-www-form-urlencoded',
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


ACTIVE = []      # 健康探测后确定可用的端点


def run_batch(fma_ids):
    """依次尝试可用端点；全部失败才返回错误。"""
    last_err = None
    for endpoint in ENDPOINTS:
        if endpoint not in ACTIVE:
            continue
        for attempt in range(RETRY + 1):
            try:
                payload = _post(endpoint, build_query(fma_ids), timeout=TIMEOUT)
                hits = {}
                for row in payload['results']['bindings']:
                    fma = 'FMA' + row['fma']['value']   # 补回前缀，对齐 concept.id
                    label = row['label']['value'].strip()
                    lang = row.get('label', {}).get('xml:lang', 'zh')
                    if not label:
                        continue
                    rank = LANG_RANK.get(lang, 5)
                    if fma not in hits or rank < hits[fma][1]:
                        hits[fma] = (label, rank, lang)
                out = {}
                for fma, (label, rank, lang) in hits.items():
                    if _to_simplified:
                        out[fma] = _to_simplified(label, 'zh-cn')      # 统一转简体
                    elif lang in SIMPLIFIED_LANGS:
                        out[fma] = label                               # 降级：只收简体变体
                    # 降级路径下，仅有繁体变体的条目直接丢弃，宁缺毋滥
                return out, None
            except Exception as exc:  # noqa: BLE001 网络错误种类繁多，统一重试
                last_err = '%s: %s' % (type(exc).__name__, exc)
                if attempt == RETRY:
                    break
                time.sleep(PAUSE * (attempt + 1))
    return {}, last_err or 'unreachable'


PROBE_Q = 'SELECT ?s WHERE { ?s <http://www.wikidata.org/prop/direct/P1402> ?o } LIMIT 1'


def probe_endpoints():
    """启动时一次性探测各端点，剔除被墙/超时的，避免每批都白等超时。"""
    alive = []
    for endpoint in ENDPOINTS:
        try:
            _post(endpoint, PROBE_Q, timeout=12)
            print('  [OK] %s' % endpoint)
            alive.append(endpoint)
        except urllib.error.HTTPError as exc:
            print('  [HTTP %s] %s' % (exc.code, endpoint))
        except Exception as exc:  # noqa: BLE001
            print('  [超时/不可达] %s (%s)' % (endpoint, type(exc).__name__))
    return alive


def main():
    global ACTIVE
    dry = '--dry' in sys.argv
    atlas = json.load(open(ATLAS))
    fma_ids = sorted({c['id'] for c in atlas['concepts']} | {p['conceptId'] for p in atlas['parts']})
    print('待查询 FMA 编号：%d 个' % len(fma_ids))

    print('探测可用端点：')
    ACTIVE = probe_endpoints()
    if not ACTIVE:
        print('\n所有 Wikidata 端点均不可用（被墙/限流/超时），终止。')
        print('建议：更换网络环境，或隔日重试。')
        return
    if _to_simplified:
        print('简繁处理：zhconv 已就绪，全部标签统一转简体。')
    else:
        print('简繁处理：未安装 zhconv，降级为只采纳简体变体（pip install zhconv 可提升命中）。')

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
