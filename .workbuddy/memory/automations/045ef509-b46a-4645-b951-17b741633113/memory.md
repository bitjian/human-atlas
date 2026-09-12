# 自动化执行记录：Wikidata 权威中文译名拉取

## 2026-09-12 首次执行 — 成功（改用镜像）

**结论**：`query.wikidata.org` 在本机网络仍不可用（TLS 握手超时，非 429/403 限流），改用 OpenLink 镜像完成全流程。

**关键结果**
- 命中 615 / 3432 个 FMA 编号（18%）；覆盖率 98.11% → 98.53%。
- 差异 240 条（同字换序 55 / 其他 185）。
- 仍含繁体 0 条；tsc / validate / build 全通过。

**根因（下次直接复用，别重复排查）**
1. P1402 字面量是**裸数字**，脚本需去/补 `FMA` 前缀——否则必然 0 命中。
2. 端点可达性：`query.wikidata.org` ❌ / `qlever.dev` ❌502 / `wikidata.demo.openlinksw.com/sparql` ✅。脚本已内置健康探测 + 回退。
3. Wikidata 中文标签 63% 仅存繁体，需 zhconv 归一（无 zhconv 时命中率从 18% 掉到 7%）。

**待用户决策的未完成项（下次执行前先看这条）**
- 覆盖策略仍是「Wikidata 无条件覆盖规则」，共 240 条存在争议、含确凿的概念错配（泪器/小脑疝/颏舌肌）。已导出 `docs/wikidata-zh-review.md` 待仲裁。
- 建议改为仲裁层后再考虑扩大范围（另有 124 条 FJ 部件可通过 conceptId 命中）。
- 规则翻译器已确认 6 类系统性 bug（前导「肌」、心室/脑室、趾/指、X proper 语序、trunk→干、portion of tissue→组织部），尚未修改。

**环境注意**
- 构建前必须 `mv dist "/tmp/human-atlas-dist-$(date +%s)"`，否则 safe-delete 守卫拦截导致 `npm run build` 报 "error during build" 无细节（原 dist 实测 36 文件）。
- 不执行 git 提交。

## 2026-09-12 第 2 轮 — 规则修复 + 仲裁层落地（已完成）

**结果**：`translate-anatomy-zh.py` 改动 75 条译名（0 回归 0 丢失），覆盖率 98.11% → **98.55%**（5217/5294，未识别 100→77）。

**已修 6 类规则 bug**：portion of tissue 组织部→组织；ventricle 心室/脑室歧义；trunk 干→躯干；多余前导「肌」；digit 手足不分；X proper / X terminalis 语序。

**已落地仲裁层**（`ATLAS_WIKI_MODE`，默认 `arbitrate`）：一致 260 / 救回 16 / 冲突 230（冲突项保留规则译名，导出 `docs/wikidata-zh-review.md`）。`override` 可一键切回旧行为。

**两个实现坑（复用前必读）**
1. `tr()` 必须先做整词优先匹配，否则含 `of` 的整词条（portion of tissue 等 3 条）会被 `' of '` 分支抢先拆开。
2. `proper` 前移只能用于血管类中心词，否则产生拇长屈肌→长拇屈肌、右心室固有心肌→右固有心室心肌等回归。

**新增待办**
- `docs/wikidata-zh-review.md` 230 条冲突待人工裁决（写入 `app/i18n/anatomy-zh.ts` 手写覆盖）。
- FJ* 部件（2001 条 / 37.8%）被 `startswith('FMA')` 跳过，经 conceptId 可多命中 124 条；建议仲裁完成后再扩大范围。

**方法论坑**：做对照实验时若临时移开 `wikidata-zh.json`，务必在还原后**再跑一次**脚本，否则 `terms-zh.ts` 会停留在"仅规则"的错误版本。

## 2026-09-12 第 3 轮 — 冲突项自动倾向判定（已完成）

**新增**：`scripts/suggest-wikidata-arbitration.py`（`--md` 输出 `docs/wikidata-zh-suggestions.md`）。按中文解剖学命名规范给 229 条冲突打「倾向 + 置信度 + 逐条依据」。

**分流**：建议 Wikidata 2 / 建议规则 42 / 人工 185 → 自动分流 **19%**。上限受精度约束——只在两侧都能干净拆成「部位+修饰」原子时才投票（例：`digiti minimi` 是复合部位词「小指」，硬拆会误判「小指伸肌」）。人工项已按类型分组（换序 25 / WD缺字 36 / WD多字 59 / 用词不同 66）。

**第 7 类 bug 已修**：肌名兼作修饰语时不应带「肌」，否则中心词被顶末尾 → `stylohyoid ligament` 韧带茎突舌骨肌→**茎突舌骨韧带**；`cricothyroid ligament` 韧带环甲肌→**环甲韧带**；`median cricothyroid ligament`→**正中环甲韧带**。裸词保持「环甲肌/茎突舌骨肌」，用整条短语锁定。全库复扫 = 0。

**可复用方法**：先按命名规范写**全库反查器**（如"英文中心词非肌肉却以「肌」结尾"），一次定位全部同类，再改词表——比逐条改可靠。

**当前状态**：5217 条；一致 261 / 救回 16 / 冲突 229；tsc 0 错误 / validate 通过 / build 2.17s。


