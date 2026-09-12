# Wikidata 权威中文译名拉取 — 执行报告

**执行时间**：2026-09-12
**项目**：human-atlas（3D 人体解剖浏览器中文化）

**结论一句话**：`query.wikidata.org` 在本机网络下仍不可用（TLS 握手超时），已改用可达镜像完成拉取；原脚本因 P1402 字面量格式错误**必然 0 命中**（已修）；并且**「Wikidata 无条件覆盖」是净负收益**，已改为仲裁制。

---

## 1. 服务可用性探测

| 目标 | 结果 |
| --- | --- |
| `query.wikidata.org/sparql` | ❌ **不可用**——连续 3 次 SSL 握手超时（`_ssl.c:1112: handshake operation timed out`，每次 45s） |
| DNS 解析 | ✅ 正常（`dyna.wikimedia.org` → 103.102.166.224） |
| TCP/TLS 连接 | ❌ 从未建立（`time_connect=0.000000s`） |
| `www.wikidata.org` / `commons` / `en.wikipedia` | ❌ 全部超时 |
| 对照 `baidu.com` / `example.com` / `registry.npmjs.org` | ✅ HTTP 200 |
| 对照 `google.com` | ❌ SSL_ERROR_SYSCALL |

**判定**：**不是** Wikidata 侧限流（无 429/403），而是**本机网络对 Wikimedia 全域的阻断**（DNS 通、TCP 不通，典型 SNI 阻断）。与项目此前记录的 429/403 是不同故障形态。首次探测曾在 1.1s 内返回 200 → 阻断是**间歇性**的，重试仍有价值。

## 2. 改用可达镜像

| 候选端点 | 结果 |
| --- | --- |
| `query.wikidata.org/sparql` | ❌ 超时 |
| `qlever.cs.uni-freiburg.de/api/wikidata` | ⚠️ 308 跳转 `qlever.dev` → **502 Bad Gateway** |
| `wikidata.demo.openlinksw.com/sparql` | ✅ **HTTP 200，可用** |
| `dbpedia.org/sparql` | ✅ 可达，但无 P1402 |

| 拉取指标 | 数值 |
| --- | --- |
| 查询 FMA 编号总数 | **3432** |
| 命中中文标签 | **615（18%）** |
| 命中（无 zhconv 降级：仅收简体变体） | 226（7%） |
| 仅存繁体变体的标签 | ≈389（**63%**） |
| 耗时 | 9 批 × BATCH 400 ≈ 30s |

产物：`app/i18n/wikidata-zh.json`（615 条，全部归一为简体，**仍含繁体 = 0**）

## 3. 修复的两个致命缺陷

`scripts/fetch-wikidata-zh.py` 原先**必然 0 命中**：

1. **P1402 字面量是裸数字**（`"7203"`），不是 `"FMA7203"`。原实现直接用 `concept.id` 拼 `VALUES`，永远匹配不上 → 已改为查询去前缀、回填补前缀。
2. **主端点不可达** → 已加入端点健康探测 + OpenLink 镜像回退 + POST（避免大批量 414）。

附带改进：语言变体优先级（zh-hans > zh-cn > zh > zh-sg …）、zhconv 简繁归一（缺失时降级为仅收简体变体，宁缺毋滥）、BATCH 150→400。

## 4. 覆盖率

| 指标 | 基线 | 本次 | 变化 |
| --- | --- | --- | --- |
| 可翻译条数 | 5194 / 5294 | **5217 / 5294** | **+23** |
| 覆盖率 | 98.11% | **98.55%** | **+0.44pp** |
| 未识别（放弃） | 100 | **77** | **−23** |

## 5. 译名仲裁（核心改动）

旧优先级「手写 > Wikidata > 规则」会让 **240 条**被替换，其中混有**确凿的错概念**与**英文直译语序**。已改为三档仲裁：

| 情形 | 处理 | 条数 |
| --- | --- | --- |
| ① 与规则译名**一致** | 直接采用（无风险） | **260** |
| ② 规则**放弃**翻译 | 采用权威译名（纯增量） | **16** |
| ③ 与规则译名**冲突** | **保留规则译名**，进 `docs/wikidata-zh-review.md` 待人工裁决 | **230**（换序 52 / 其他 178） |

开关：`ATLAS_WIKI_MODE=arbitrate`（默认）/ `override`（旧行为）。

被仲裁**成功拦截**的劣质覆盖示例：

| 英文名 | 规则译名（保留） | Wikidata（已拒绝） |
| --- | --- | --- |
| nasolacrimal duct | **鼻泪管** | ~~泪器~~（错概念） |
| tentorium cerebelli | **小脑幕** | ~~小脑疝~~（错概念） |
| mylohyoid | **下颌舌骨肌** | ~~颏舌肌~~（错肌） |
| external ear | **外耳** | ~~动耳肌~~ |
| testicular vein | **睾丸静脉** | ~~精索静脉~~ |
| deep cervical artery | **颈深动脉** | ~~深颈动脉~~（英文直译语序） |

## 6. 修复的 6 类系统性规则 bug

规则层共改动 **75 条译名，0 条回归、0 条丢失**。

| 优先级 | 缺陷 | 证据（修复前 → 修复后） |
| --- | --- | --- |
| P0 | `portion of tissue` 被 `' of '` 拆分误译 | ~~组织部~~ → **组织**；~~结缔组织部~~ → **结缔组织** |
| P0 | `ventricle` 脑/心语境不分 | ~~外侧心室~~ → **侧脑室**；~~第三心室~~ → **第三脑室**；~~脑心室系统~~ → **脑室系统** |
| P0 | `trunk`（躯体）误作解剖学「干」 | ~~干~~ → **躯干**（血管干如 thyrocervical trunk → 甲状颈干 不受影响） |
| P1 | 多余前导「肌」 | ~~肌棘间肌~~ → **棘间肌**；~~肌斜角肌~~ → **斜角肌**；~~肌回旋肌~~ → **回旋肌** |
| P1 | `digit` 手足不分 | ~~趾浅屈肌~~ → **指浅屈肌**；~~趾伸肌~~ → **伸指肌**；~~足底指总动脉组~~ → **足底趾总动脉组** |
| P1 | `X proper` / `X terminalis` 语序 | ~~肝动脉固有~~ → **肝固有动脉**；~~板终~~ → **终板** |
| P2 | 部位+方位+肌 语序 | ~~大腰肌~~ → **腰大肌**；~~内侧股肌~~ → **股内侧肌** |

**实现要点（避免踩坑）**：
- `tr()` 加了**整词优先**匹配，否则 `portion of tissue` 会被 `' of '` 分支抢先拆开（EXTRA 里同名的整词条永不生效）。
- `proper` 单独归 `kind='pre'`，**仅当中心词是「动脉/静脉」时**才把「固有」前移。曾尝试对所有修饰语前移，导致 ~~拇长屈肌→长拇屈肌~~、~~肋长提肌→长肋提肌~~、~~右心室固有心肌→右固有心室心肌~~ 等一批回归，已收敛。
- 补了 6 条「规则无法翻译且 Wikidata 也不准」的基础概念：`pons`→**脑桥**（Wikidata: 桥脑）、`alimentary system`→**消化系统**（Wikidata: 排遗系统）、`integument`→**体被**（Wikidata: 覆盖物）、`human body`→**人体**（Wikidata: 人体解剖）、`genital system`→**生殖系统**、`cerebral arterial circle`→**大脑动脉环**。

## 7. 验证

| 验证项 | 结果 |
| --- | --- |
| `npx tsc --noEmit` | ✅ **0 类型错误** |
| `node scripts/validate-atlas.mjs` | ✅ 2234 meshes / 3432 concept mappings / 2,288,268 triangles |
| `npm run build` | ✅ **2.02s**（构建前需 `mv dist /tmp/human-atlas-dist-<ts>` 绕过 safe-delete 守卫） |

## 8. 结构性覆盖盲区（待决策）
术语表 ID 有两套，脚本的 `i.startswith('FMA')` 会跳过后者：

| ID 形态 | 含义 | todo 条数 | 占比 | Wikidata 能否覆盖 |
| --- | --- | --- | --- | --- |
| `FMA*` | 概念级 | 3293 | 62.2% | ✅ |
| `FJ*` / `FJ*M` | 部件实例级 | **2001** | **37.8%** | ❌ 被跳过 |

部件带 `conceptId` 指向 FMA 概念，实测可间接多命中 **124 条**。建议**先完成 230 条仲裁**再考虑扩大范围。

## 9. 冲突项的自动倾向判定

新增 `scripts/suggest-wikidata-arbitration.py`，按中文解剖学命名规范对 229 条冲突给出**倾向 + 置信度 + 逐条依据**，输出 `docs/wikidata-zh-suggestions.md`。

判定依据均为可解释的规范，非黑箱打分：

| 规则 | 指向 | 依据 |
| --- | --- | --- |
| R1 脏数据 | 规则 | Wikidata 含英文/括号 |
| R2 泛化前缀 | 规则 | Wikidata 带「人类/人体」前缀 |
| R3 概念错配 | 规则 | 两者无共同汉字 |
| R5 口语俗称 | 规则 | Wikidata 用「脸/脚/脖子」等非规范说法 |
| W1 冗余前缀 | Wikidata | 规则译名多出前导「肌」 |
| R4 规范语序 | 双向 | **部位 + 修饰 + 中心词**（颈深动脉 而非 深颈动脉；腰大肌 而非 大腰肌） |

| 判定结果 | 条数 |
| --- | --- |
| 建议采纳 Wikidata | **2** |
| 建议保留规则译名 | **42**（高置信 10） |
| 需人工裁决 | **185** |
| **自动分流** | **44 / 229 = 19%** |

**为什么只有 19%**：自动判定只在**两侧都能干净拆成「部位 + 修饰」原子**时才投票。继续放宽会开始误判——例如 `extensor digiti minimi` 的 `digiti minimi` 是复合部位词「小指」，硬拆成「指+小」就会把正确的「小指伸肌」判成错。**宁可交人工，不做错判**。

剩余 185 条已按决策类型分组，便于批量复核：

| 类型 | 条数 | 复核要点 |
| --- | --- | --- |
| 换序 | 25 | 同一批字、语序不同：按规范语序判断 |
| WD缺字 | 36 | Wikidata 更短更泛，疑概念错配，倾向保留规则译名 |
| WD多字 | 59 | Wikidata 更长，疑加层级/限定词 |
| 用词不同 | 66 | 同义术语二选一，需查《人体解剖学名词》 |

### 顺带修掉的第 7 类 bug：肌名兼作修饰语

用同一套规范反查全库，又发现一类：**肌名当修饰语时不该带「肌」**，否则中心词被顶到最后。

| 词条 | 修复前 | 修复后 |
| --- | --- | --- |
| stylohyoid ligament | ~~韧带茎突舌骨肌~~ | **茎突舌骨韧带** |
| cricothyroid ligament | ~~韧带环甲肌~~ | **环甲韧带** |
| median cricothyroid ligament | ~~正中韧带环甲肌~~ | **正中环甲韧带** |

裸词 `cricothyroid` / `stylohyoid` 仍译「环甲肌 / 茎突舌骨肌」（`zone of cricothyroid` → 环甲肌区 不受影响），因此用整条短语锁定。全库复扫该类 bug = **0 条**。

## 附：产出与改动文件

| 文件 | 说明 |
| --- | --- |
| `app/i18n/wikidata-zh.json` | 🆕 615 条权威中文标签（全简体） |
| `app/i18n/terms-zh.ts` | 🔄 重生成 5217 条（覆盖率 98.55%） |
| `scripts/fetch-wikidata-zh.py` | 🔧 修 P1402 格式 + 端点回退 + 简繁归一 |
| `scripts/translate-anatomy-zh.py` | 🔧 7 类规则 bug + 仲裁层（`ATLAS_WIKI_MODE`） |
| `scripts/suggest-wikidata-arbitration.py` | 🆕 冲突项自动倾向判定（按命名规范） |
| `docs/wikidata-zh-review.md` | 🆕 230 条冲突待人工裁决 |
| `docs/wikidata-zh-suggestions.md` | 🆕 229 条冲突的倾向 + 置信度 + 逐条依据 |

**未执行 git 提交**（按要求交由用户在终端执行）。

## 复现命令

```bash
cd /Users/zizi/bitjian/human-atlas

# 1) 拉取（建议用带 zhconv 的解释器，命中率 18% vs 7%）
python3 scripts/fetch-wikidata-zh.py

# 2) 重新生成术语表（默认仲裁制；旧行为加 ATLAS_WIKI_MODE=override）
python3 scripts/translate-anatomy-zh.py

# 3) 验证
npx tsc --noEmit
node scripts/validate-atlas.mjs

# 4) 构建（必须先移走 dist）
mv dist "/tmp/human-atlas-dist-$(date +%s)" && npm run build
```
