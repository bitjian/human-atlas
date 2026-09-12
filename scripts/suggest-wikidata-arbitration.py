# -*- coding: utf-8 -*-
"""对「规则译名 vs Wikidata 权威译名」冲突项做自动倾向判定，压缩人工裁决量。

背景：app/i18n/terms-zh.ts 由 scripts/translate-anatomy-zh.py 生成，其中与
Wikidata 权威译名冲突的条目当前一律保留规则译名（策略 arbitrate）。逐条人工
裁决成本高，本脚本按中文解剖学命名规范给出**倾向建议 + 置信度**。

判定依据（全部为可解释的命名规范，而非黑箱打分）：

  倾向「规则」
    R1 脏数据     Wikidata 标签含英文/括号/标点（如「副交感神经节（parasympathetic ganglion）」）
    R2 泛化前缀   Wikidata 标签带「人类/人体/人」前缀（如「人类鼻子」）
    R3 概念错配   两者无共同汉字 → 很可能指的不是同一个结构（如 鼻泪管 vs 泪器）
    R4 血管语序   同为「部位+方位+动脉/静脉」与「方位+部位+动脉/静脉」的换序，
                  中文规范取前者（颈深动脉 而非 深颈动脉；胃左动脉 而非 左胃动脉）

  倾向「Wikidata」
    W1 冗余前缀   规则译名以「肌」开头而权威译名不以（如 肌斜角肌 → 斜角肌）
    W2 肌名语序   同为「修饰+部位+肌」与「部位+修饰+肌」的换序，
                  中文规范取后者（腰大肌、股内侧肌 而非 大腰肌、内侧股肌）

  其余 → 「人工」，不给倾向。

用法：
  python3 scripts/suggest-wikidata-arbitration.py            # 打印统计 + 建议分布
  python3 scripts/suggest-wikidata-arbitration.py --md OUT   # 写出带建议列的清单
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 命名规范用词表 -------------------------------------------------------
# 方位 / 修饰（出现在「部位」之前或之后都合法，但含义不同）
MOD = set("""上 下 前 后 内 外 深 浅 左 右 中 侧 近 远 大 小 长 短 最 主 副 总 固有
内侧 外侧 中间 最上 最下 前上 前下 后上 后下 上内 上外 下内 下外 背侧 腹侧
掌侧 足底 浅 深 桡侧 尺侧 胫侧 腓侧 前上 后下 上段 中段 下段""".split())
# 部位 / 器官（血管、神经、肌名的规范语序是「部位在前」）
PART = set("""腰 胸 臀 股 头 颈 腹 背 肩 臂 腿 足 手 肢 指 趾 肋 喉 咽 腭 舌 眼 耳 鼻
颏 颊 唇 胃 肝 脾 胰 肾 肠 骨 踝 腕 肘 膝 盆 椎 骶 髂 桡 尺 胫 腓 肱 颞 枕 额 顶
眶 筛 蝶 心 肺 胆 膈 跖 掌 舟 距 跟 髋 阴 睾 卵 巢 前庭 鼓 蜗 会厌 咬 滑车
甲状腺 肾上腺 肠系膜 咽鼓管 斜方 肩胛 锁骨 胸骨 舌骨 甲状 环状 环甲 环杓 杓
腭帆 食管 气管 支气管 主动脉 肺动脉 冠状动脉 门 胆囊 输尿 膀胱 子宫 阴道
直肠 结肠 盲肠 空肠 回肠 十二指肠 乙状结肠 骨间 掌骨 跖骨 额叶 颞叶 顶叶 枕叶
脉络丛 扣带 海马 脑 小脑 大脑 丘脑 延髓 中脑 垂体 松果 脊髓 神经 皮质
口腔 皮肤 骨骼 肌 颅 面 眶 颧 腭 咽 喉 声带 腮腺 下颌 上颌""".split())
# 肌肉类后缀（先于单纯「肌」剥离，避免「缩肌/屈肌」被当成修饰语）
MUSCLE_CLASS = ('括约肌', '对掌肌', '回旋肌', '轮匝肌', '缩肌', '提肌', '屈肌',
                '伸肌', '展肌', '收肌', '斜肌', '直肌', '张肌', '方肌', '匝肌')
# 中心词（血管 / 神经 / 管道 / 肌）
CENTER = ('动脉', '静脉', '神经', '干', '韧带', '回', '肌')
# 口语/俗称词：中文解剖学名词规范不用这些说法
COLLOQUIAL = ('脸', '脚', '脖子', '肚子', '骨头', '鼻子', '嘴巴', '个头')


def _strip_center(s):
    """剥离中心词，返回 (中心词, 词干)；无中心词则返回 (None, s)。"""
    for c in MUSCLE_CLASS:
        if s.endswith(c) and len(s) > len(c):
            return '肌', s[:-len(c)]
    for c in CENTER:
        if s.endswith(c) and len(s) > len(c):
            return c, s[:-len(c)]
    return None, s


def _split_mod_part(s):
    """把「部位+修饰」或「修饰+部位」拆开；拆不出返回 None。"""
    for k in range(1, len(s)):
        a, b = s[:k], s[k:]
        if a in PART and b in MOD:
            return ('PM', a, b)      # 部位 + 修饰（规范语序）
        if a in MOD and b in PART:
            return ('MP', a, b)      # 修饰 + 部位（英文直译语序）
    return None


def judge(name, rule, wiki):
    """返回 (倾向, 置信度, 规则列表)。倾向 ∈ {'规则','Wikidata','人工'}。"""
    votes, reasons = [], []

    def vote(side, weight, why):
        votes.append((side, weight))
        reasons.append('%s(%+d)：%s' % (side, weight, why))

    # ---- R1 脏数据 ----
    if re.search(r'[A-Za-z()（）\[\]{}]', wiki):
        vote('规则', 3, 'Wikidata 含英文/括号，数据不洁')

    # ---- R2 泛化前缀 ----
    if re.match(r'^(人类|人体|人的)', wiki):
        vote('规则', 2, 'Wikidata 带「人类/人体」泛化前缀')

    # ---- R3 概念错配：无共同汉字 ----
    if not (set(rule) & set(wiki)):
        vote('规则', 3, '两者无共同汉字，疑概念错配')

    # ---- R5 口语/俗称 ----
    if wiki in COLLOQUIAL or wiki.endswith('脚'):
        vote('规则', 2, 'Wikidata 用口语俗称（%s），规范名词不用' % wiki)

    # ---- W1 规则冗余「肌」前缀 ----
    if rule.startswith('肌') and not wiki.startswith('肌'):
        vote('Wikidata', 2, '规则译名多出前导「肌」')

    # ---- R4/W2 规范语序：部位 + 修饰 + 中心词 ----
    # 同一原理双向适用：符合规范的得票，不符合的失分。
    kind_r, stem_r = _strip_center(rule)
    kind_w, stem_w = _strip_center(wiki)
    if kind_r and kind_r == kind_w and sorted(rule) == sorted(wiki):
        r, w = _split_mod_part(stem_r), _split_mod_part(stem_w)
        if r and w and r[0] == 'PM' and w[0] == 'MP':
            vote('规则', 2, '规范语序取「部位+修饰」（%s）而非「修饰+部位」（%s）'
                 % (rule, wiki))
        elif r and w and r[0] == 'MP' and w[0] == 'PM':
            vote('Wikidata', 2, '规范语序取「部位+修饰」（%s）而非「修饰+部位」（%s）'
                 % (wiki, rule))

    if not votes:
        return '人工', '-', reasons

    rule_score = sum(w for s, w in votes if s == '规则')
    wiki_score = sum(w for s, w in votes if s == 'Wikidata')
    if rule_score == 0 and wiki_score == 0:
        return '人工', '-', reasons
    if rule_score == 0:
        side = 'Wikidata'
    elif wiki_score == 0:
        side = '规则'
    else:
        return '人工', '-', reasons + ['（双向都有信号，交人工）']
    conf = '高' if abs(rule_score - wiki_score) >= 3 else '中'
    return side, conf, reasons


def classify(rule, wiki):
    """给人工项标注决策类型，便于批量复核。"""
    if sorted(rule) == sorted(wiki):
        return '换序'          # 同一批字、不同语序：按规范「部位+修饰+中心词」裁决
    if set(wiki) <= set(rule):
        return 'WD缺字'        # Wikidata 更短/更泛，疑概念错配
    if set(rule) <= set(wiki):
        return 'WD多字'        # Wikidata 更长，疑加了限定或层级词
    return '用词不同'          # 同义术语二选一，需查名词规范


def collect():
    """复用翻译脚本的规则引擎，收集全部冲突项。"""
    src = open(os.path.join(ROOT, 'scripts/translate-anatomy-zh.py')).read()
    G = {'__name__': 'not_main',
         '__file__': os.path.join(ROOT, 'scripts/translate-anatomy-zh.py')}
    exec(compile(src.split('if len(sys.argv) > 1:')[0], 't', 'exec'), G)
    translate = G['translate']

    atlas = json.load(open(os.path.join(ROOT, 'public/models/atlas.json')))
    hand = open(os.path.join(ROOT, 'app/i18n/anatomy-zh.ts')).read()
    have = set(re.findall(r'(F[JM]A?\d+):', hand.split('export const ANATOMY_ZH')[1]))
    entries = ([(p['id'], p['name']) for p in atlas['parts']]
               + [(c['id'], c['name']) for c in atlas['concepts']])
    wiki_all = json.load(open(os.path.join(ROOT, 'app/i18n/wikidata-zh.json')))

    rows = []
    for i, n in entries:
        if i in have or not i.startswith('FMA'):
            continue
        w = wiki_all.get(i)
        if not w:
            continue
        r = translate(n)
        if r and r != w:
            rows.append((i, n, r, w))
    return sorted(rows, key=lambda x: x[1])


def main():
    md_out = None
    if '--md' in sys.argv:
        md_out = sys.argv[sys.argv.index('--md') + 1]

    rows = collect()
    buckets = {'规则': [], 'Wikidata': [], '人工': []}
    for i, n, r, w in rows:
        side, conf, why = judge(n, r, w)
        # 高置信且建议采纳 Wikidata 才算「建议采纳」，降低误伤
        buckets[side].append((i, n, r, w, conf, why))

    print('冲突总数：%d' % len(rows))
    for side in ('Wikidata', '规则', '人工'):
        hi = sum(1 for x in buckets[side] if x[4] == '高')
        mid = sum(1 for x in buckets[side] if x[4] == '中')
        print('  建议 %-9s %3d 条（高置信 %d / 中置信 %d）'
              % (side, len(buckets[side]), hi, mid))
    auto = len(buckets['Wikidata']) + len(buckets['规则'])
    print('  → 自动分流 %d 条（%.0f%%），仍需人工 %d 条（%.0f%%）'
          % (auto, 100.0 * auto / len(rows),
             len(buckets['人工']), 100.0 * len(buckets['人工']) / len(rows)))

    print('\n=== 建议采纳 Wikidata（前 20）===')
    for i, n, r, w, conf, why in buckets['Wikidata'][:20]:
        print('  [%s] %-40s 规则:%-14s → %s' % (conf, n[:40], r, w))
    print('\n=== 建议保留规则（前 20）===')
    for i, n, r, w, conf, why in buckets['规则'][:20]:
        print('  [%s] %-40s 规则:%-14s (Wikidata:%s)' % (conf, n[:40], r, w))

    if md_out:
        L = ['# Wikidata 冲突项 — 自动倾向判定清单', '',
             '由 `scripts/suggest-wikidata-arbitration.py` 生成。判定依据为中文解剖学',
             '命名规范（部位前置、方位词位置、概念一致性、数据清洁度），每条均附理由。', '',
             '| 建议 | 条数 | 高置信 | 中置信 |', '| --- | --- | --- | --- |']
        for side in ('Wikidata', '规则', '人工'):
            hi = sum(1 for x in buckets[side] if x[4] == '高')
            mid = sum(1 for x in buckets[side] if x[4] == '中')
            L.append('| %s | %d | %d | %d |' % (side, len(buckets[side]), hi, mid))
        # 人工项的决策类型分布
        kinds = {}
        for x in buckets['人工']:
            kinds.setdefault(classify(x[2], x[3]), 0)
            kinds[classify(x[2], x[3])] += 1
        L += ['', '## 待人工项的决策类型分布', '',
              '| 类型 | 条数 | 复核要点 |', '| --- | --- | --- |',
              '| 换序 | %d | 同一批字、语序不同：按「部位+修饰+中心词」判断 |' % kinds.get('换序', 0),
              '| WD缺字 | %d | Wikidata 更短更泛，疑概念错配，倾向保留规则译名 |' % kinds.get('WD缺字', 0),
              '| WD多字 | %d | Wikidata 更长，疑加了层级/限定词，逐条判断 |' % kinds.get('WD多字', 0),
              '| 用词不同 | %d | 同义术语二选一，需查《人体解剖学名词》 |' % kinds.get('用词不同', 0)]
        for side, title in (('Wikidata', '建议采纳 Wikidata'),
                            ('规则', '建议保留规则译名'),
                            ('人工', '需人工裁决')):
            L += ['', '## %s（%d 条）' % (title, len(buckets[side])), '',
                  '| 建议 | 置信 | 类型 | FMA | 英文名 | 规则译名 | Wikidata | 依据 |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- |']
            for i, n, r, w, conf, why in buckets[side]:
                L.append('| %s | %s | %s | %s | %s | %s | %s | %s |'
                         % (side, conf, classify(r, w), i, n, r, w, '；'.join(why)))
        open(md_out, 'w').write('\n'.join(L) + '\n')
        print('\n已写入 %s' % md_out)


if __name__ == '__main__':
    main()
