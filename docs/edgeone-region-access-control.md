# 限制访问区域：只允许国内用户访问

站点：`body3d.bitjian.cn`（EdgeOne Pages，代码源 `my-tweaks`，加速区域 = 全球可用区（含中国大陆））

---

## 一、先厘清概念：加速区域 ≠ 访问控制

**加速区域管的是"用哪些节点给你加速"，不管"谁能访问"。**

| 加速区域 | 节点范围 | 自定义域名备案 | 实际可访问范围 |
|---|---|---|---|
| 中国大陆可用区 | 仅中国大陆节点 | 必须备案 | 全球都能访问（海外用户走大陆节点，慢） |
| **全球可用区（含中国大陆）** ← 当前 | 大陆节点 + 国际节点 | 必须备案 | **全球都能访问**（各走就近节点，最快） |
| 全球可用区（不含中国大陆） | 仅国际节点 | 无需备案 | 海外可访问，**中国大陆返回 401** |

所以当前配置 = 国内和海外用户都能访问。如果你想的是"只有国内能访问"，**加速区域里没有这个选项**，需要通过访问控制实现。

> 注意方向相反的那个需求：如果你其实想"只让海外访问"，把加速区域改成「全球可用区（不含中国大陆）」就行，国内会直接 401，而且不用备案。那是唯一一个靠加速区域本身能达成的方向。

---

## 二、方案一（推荐 · 零代码）：控制台自定义规则

EdgeOne Pages 正式版自带安全防护，免费版有 **5 条自定义规则**额度，其中明确支持**地域限制**。

路径：`Pages 控制台 → 该项目 → 左侧「安全防护」→「自定义规则」→ 添加规则`

| 配置项 | 取值 |
|---|---|
| 域名 | `body3d.bitjian.cn` |
| 匹配条件（规则类型） | 地域 / 客户端 IP 所属区域 |
| 运算符（匹配方式） | **不包含**（区域不匹配） |
| 匹配内容 | 中国大陆（全部） |
| 执行动作（处置方式） | **拦截** |

含义：命中"来源 IP 不在中国大陆"的请求 → 直接拦截。中国大陆访客不匹配该规则，正常放行。

### ⚠️ 关键：Pages 的控制台长什么样（2026-09 实测截图）

Pages 版「自定义规则 → 添加规则」的实际下拉项，和站点版 EdgeOne 不一样：

- **匹配类型**只有 5 项：`客户端 IP` / `Referer` / `User-Agent` / `ASN` / `URL`
- 选中「客户端 IP」时，**匹配方式只有 2 项**：`匹配` / `不匹配`
- 匹配内容是**纯 IP 输入框**，官方提示语原文：「输入 IP，支持 IP 及 IP 段（回车分隔多个值），多个值中匹配其一则为命中」

也就是说：**「客户端 IP」这一项只能按 IP / IP 段判断，不能按国家或地区判断。** 想用它实现"只放行中国内地"，就得把中国内地所有 IP 段都列出来——而 EdgeOne 规则引擎限制**单条规则匹配项数量总和 ≤ 128 个**（见[匹配条件](https://edgeone.ai/zh/document/55940)），中国内地 IPv4 段有上千条，塞不下，**这条路走不通**。

所以要不要用控制台，取决于一件事——**「匹配类型」下拉里到底有没有「区域管控」**（部分版本叫「地域」）：

| 下拉里有「区域管控」 | 怎么填 |
|---|---|
| 域名 | `body3d.bitjian.cn` |
| 规则名称 | `国外流量拦截` |
| 匹配类型 | **区域管控**（滚动下拉到底确认） |
| 匹配方式 | **区域不包含**（或「客户端 IP 区域不包含」） |
| 匹配内容 | `中国大陆（全部）` |
| 执行动作 | `拦截` |
| 状态 | 开启 |

填完语义读作：「客户端 IP 的**地域不属于**中国内地 → 拦截」。读得通就对了。

**如果下拉里没有「区域管控」**：控制台这条路实现不了地域限制，走第三节的 `middleware.js`（Pages 官方明确支持基于 `context.geo` 做地域访问控制），或者给项目提交工单问一下地域规则是否只在付费版开放。

> 反向自检：**绝不要**在「客户端 IP」这一项里填 `不匹配` + 随便一个 IP 段就保存。语义是"不在这个网段内 → 拦截"，会把包括内地在内的几乎全部访客一起拦掉，站点直接不可用。
> 站点版 EdgeOne（非 Pages）的对应命名是「规则类型 = 区域管控 / 匹配方式 = 客户端 IP 区域不包含 / 处置方式 = 拦截」，语义一致。

**优点**：不写代码、不动仓库、立刻生效。
**缺点**：拦截后是平台默认 403 页面，文案不友好、无法定制。

---

## 三、方案二（可控 · 需代码）：平台中间件 middleware.js

Pages 提供**平台级通用中间件**，非全栈框架项目（本项目是 `vite build` → `dist` 纯静态）直接在项目根目录放 `middleware.js` 即可，`context.geo` 里带客户端地理位置。

**✅ 已落地**：代码就在仓库根目录 `middleware.js`（与 `package.json` 同级），推送后由 Pages 平台自动加载，不需要改 `vite.config`、也不会进 `dist`。

### 三个可调参数（都在 `middleware.js` 顶部）

| 常量 | 当前值 | 作用 | 想改的时候 |
|---|---|---|---|
| `ALLOW` | `['CN','HK','MO','TW']` | 放行的国家/地区码 | 只面向中国内地 → 删掉 `HK`/`MO`/`TW` |
| `BOT_ALLOW` | `[]`（空） | 放行搜索引擎爬虫 UA 关键字 | 想保住 Google/Bing 收录 → 填 `['googlebot','bingbot']` |
| `FAIL_OPEN` | `true` | 取不到地理位置时放行还是拦截 | 想更严格 → 改 `false`（本地 dev 也会被拦，调试时注意） |

### 官方文档已确认的接口

中间件签名 `export function middleware(context)`，`context` 含 `request / next / redirect / rewrite / geo / clientIp`；
`geo` 字段为 `asn / countryName / countryCodeAlpha2 / countryCodeAlpha3 / countryCodeNumeric / regionName / regionCode / cityName / latitude / longitude`；
`config.matcher` 支持单字符串、数组、正则。文档：<https://test-pages.edgeone.ai/zh/document/middleware>

拦截页是浅色卡片，配色直接取自 `app/globals.css`（背景 `#f3f4f4`、正文 `#20242b`、警示用 `--destructive` `#a8574a`），与站点视觉一致，中英双语。

本地调试：`npx edgeone pages dev`（`middleware.js` 里的 `console.log` 会直接打在终端，能看到每个请求的地区码）。

**注意**：本项目不是 Next.js，不要用 `middleware.ts` / `proxy.ts`（那是框架级中间件）；用平台级 `middleware.js`。文件放项目根目录，不会被 `vite build` 影响。
**另注意**：仓库里还有 `vercel.json`（上游遗留）。若将来改部署到 Vercel，根目录这个 `middleware.js` 会被 Vercel 当成 Edge Middleware 解析（它要求 default export），需要改名或删除，否则可能构建失败。仅部署 EdgeOne Pages 则无影响。

---

## 四、五个必须知道的坑

1. **港澳台是独立地区码**。IP 地理库中 `CN` / `HK` / `MO` / `TW` 并列，只放行 `CN` 会把中国香港、中国澳门、中国台湾用户一起拦掉。按需决定是否加入放行清单。
2. **搜索引擎爬虫会受影响**。Googlebot / Bingbot 走海外 IP，会被一并拦截 → **Google / Bing 收录会掉**；百度、搜狗爬虫在境内，基本不受影响。若想保留 Google 收录，需要额外放行对应 UA（自定义规则可组合，但免费版只有 5 条额度）。
3. **VPN / 代理可绕过**。区域限制基于 IP 归属，不是强隔离手段，只能"减少"而非"杜绝"境外访问。别把它当安全边界用。
4. **拦截是边缘侧前置生效**，不影响缓存策略，也不改变加速区域 —— 大陆节点照旧工作，只是不把内容发给境外 IP。
5. **与本项目的历史约束无关**：`.bin.gz` 的 `Content-Encoding` 空值要求、90MB 分块加载等照旧；中间件对每个请求多跑一次轻量判断，无实际影响。

---

## 五、合规提示

- 按来源地区做访问控制是常见的服务范围设定，**不需要事前审批**，也不改变现有备案状态。
- 真正的合规义务不受"只服务国内"影响，仍然要保留：`LICENSE`（代码 MIT）、`public/ATTRIBUTION.md`（BodyParts3D / CC BY 4.0）、UI 可见署名并**标明改编事实**、以及"教学科普、非临床诊断"的定位声明。详见 `docs/compliance-notice.md`。
- 产品名不要使用 "Human Atlas"（MIT 不授予商标许可）。

---

## 六、怎么选（已按实测更正）

| 你的目标 | 做法 |
|---|---|
| 只让中国内地访问（Pages） | **方案二（已落地）**：根目录 `middleware.js`。⚠️ 已实测 Pages 控制台**没有**地域规则，别再找「方案一」了 |
| 想保留 Google / Bing 收录 | 在 `middleware.js` 的 `BOT_ALLOW` 填 `['googlebot','bingbot']` |
| 想连港澳台一起拦 | 在 `middleware.js` 的 `ALLOW` 里删掉 `'HK','MO','TW'` |
| 其实是想"只让海外访问" | 改加速区域为「全球可用区（不含中国大陆）」，国内 401，免备案 |
| 想要图形化配置界面 | 迁到 **EdgeOne 本体（EO）** 用「区域管控」，但需接入站点 + 自备源站，成本明显更高 |

---

## 七、怎么验证（完整验证流程）

### 第一层 · 离线逻辑回归（不联网、最快）

```bash
node scripts/test-middleware.mjs    # 29 项断言；有失败则退出码 1
```

覆盖：放行清单、大小写不敏感、海外拦截、geo 缺失兜底、403 响应形态、分块路径放行时不动响应头、matcher。

**为什么必须要有这层**：`middleware.js` 是 `.js`，而 `tsconfig.json` 的 include 只有 `.ts/.tsx/.mts`，所以它**不在 `npm run check` 的检查范围内**；本地 `edgeone pages dev` 又取不到 geo（会走 `FAIL_OPEN` 全部放行），同样验证不了拦截逻辑。**改完中间件先跑这个。**

### 第二层 · 线上双端验证（必须两边都测）

> ⚠️ **只测大陆是无效验证** —— 中间件哪怕完全没加载，大陆也是 200。必须同时证明"海外被拦"。

```bash
# A. 大陆侧：期望 200（带时间戳绕开边缘缓存）
curl -s -o /dev/null -w "%{http_code}\n" "https://body3d.bitjian.cn/?_=$(date +%s)"

# B. 海外侧：多地域探测服务，期望 403
RID=$(curl -s -H "Accept: application/json" \
  "https://check-host.net/check-http?host=https%3A%2F%2Fbody3d.bitjian.cn%2F&max_nodes=8" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['request_id'])")
sleep 12
curl -s -H "Accept: application/json" "https://check-host.net/check-result/$RID"
# 返回形如 [1, 0.02, 'OK', '403', '<ip>'] —— 注意第 4 个元素才是状态码，别看错

# C. 确认 403 是"我们自己的拦截页"，而不是平台通用 403（关键一步）
curl -s "https://api.microlink.io/?url=https%3A%2F%2Fbody3d.bitjian.cn%2F"
# 检查 title=当前地区暂不可访问、description=Access restricted、
# headers.cache-control=no-store, must-revalidate
```

**必做对照实验**：把 B 里的 host 换成 `https://example.com` 再跑一次，应返回 `200`。若对照也是 403，说明是探测服务自身的问题，不是你的配置。

### 第三层 · 部署与观测

- **部署确认**：Pages 控制台 → 构建部署，确认最新部署成功；`curl -I` 看 `last-modified` 是否为新部署时间。
- **观测**：控制台「指标分析」→「访问区域分布」与状态码分布 —— 海外区域流量应消失、403 占比上升。
- **日志**：拦截时会输出 `[geo-block] region=XX ip=... -> 403`，本地 `npx edgeone pages dev` 可直接看到。

### 四个验证陷阱

1. **边缘缓存**：测之前一定加随机查询串，并确认 `eo-cache-status: Cache Miss`，否则可能命中缓存绕过中间件。
2. **只测单边**：必须"大陆 200 + 海外 403"成对验证，缺一不可。
3. **VPN**：自己挂代理测会被拦，这是预期行为，别误判为故障。
4. **港澳台**：当前 `ALLOW` 含 `HK/MO/TW`，这三地会正常放行。

### 本次实测结果（2026-09-12 存档）

| 探测源 | 地区 | 结果 |
|---|---|---|
| 本机直连（中国移动，武汉） | CN | **200** ✅ 首页 / `favicon.svg` / `/models/atlas.json` 均 200，`eo-cache-status: Cache Miss` |
| check-host.net 8 节点 | AT / DE×2 / FI / IR×2 / NL / UA | **全部 403** ✅ |
| 对照：example.com 同批节点 | AT / ES / SE / US | 200 ✅（证明探测链路正常、状态码解析无误） |
| microlink（海外） | — | **403**，`title=当前地区暂不可访问`、`description=Access restricted`、`cache-control=no-store, must-revalidate` ✅ —— 确认为自有拦截页 |

**结论：中间件已上线并生效，"大陆放行 + 海外拦截"双向验证通过。**

---

## 八、Google Search Console 接入（受地域规则影响，须特别处理）

### 为什么普通接法会失败

GSC 相关的抓取器**UA 里不含 `googlebot`**，因此**不会命中** `BOT_ALLOW`，而它们的抓取源在**海外** → 被地域规则 **403** → **验证与网址检查必然失败**。

| 抓取器 | UA | 用途 |
|---|---|---|
| Google 站点验证 | `Mozilla/5.0 (compatible; Google-Site-Verification/1.0)` | 属性所有权验证（HTML 文件 / meta 标签方式都用它抓） |
| 网址检查工具 | `Google-InspectionTool` | GSC「网址检查 / 测试实际网址」 |

**已修复（2026-09-12）**：这两个 UA 已加入 `middleware.js` 的 `BOT_ALLOW`。它们与 `googlebot` 走**同一条 gated 判定**，落在 `/models/*` 下**仍返回 403**——即白名单只用于"让搜索引擎/验证器能访问公开页面"，**不放宽未来付费门控的防护**。

> ⚠️ **顺序很重要：先把本次改动 push 部署，再去 GSC 做验证。** 部署前 `BOT_ALLOW` 里还没有这两个 UA，且 `robots.txt` / `sitemap.xml` 也还没上线。

### 验证方式对比

| 方式 | 需要什么 | 要改代码吗 | 评价 |
|---|---|---|---|
| **DNS TXT** | 在 `bitjian.cn` 的 DNS 加一条 TXT 记录 | ❌ 不需要 | **最干净**：不发 HTTP 请求，对地域拦截**天然免疫**；且可验证「网域」级属性（覆盖所有子域） |
| **HTML 文件** | 把 GSC 给的 `google<随机串>.html` 放进 `public/`（随构建发布） | ❌ 不需要 | 推荐度次之；UA 已放行 |
| meta 标签 | 把 `<meta name="google-site-verification" …>` 加进 `web/index.html` 的 `<head>` | ✅ 需要 | 会改动入口 HTML |
| GA / GTM | 站点接入 GA 或 GTM | ✅ 需要 | 依赖额外脚本 |

### 操作步骤

1. **部署先行**：push `my-tweaks` 分支，确认 Pages 构建成功。
2. **添加资源**：打开 <https://search.google.com/search-console> → 左上「添加资源」。
   - 想**只覆盖本站** → 选「**网址前缀**」，填 `https://body3d.bitjian.cn/`
   - 想**覆盖整个 `bitjian.cn` 及所有子域** → 选「**网域**」，填 `bitjian.cn`（此类型**只能**用 DNS TXT 验证）
3. **完成验证**：按上表选一种方式。走 HTML 文件就把它放进 `public/` 后重新部署；走 DNS TXT 就把 GSC 给的 TXT 值加到 DNS。
4. **提交 sitemap**：左侧「站点地图」→ 填 `sitemap.xml` → 提交。
   （`robots.txt` 里已声明 `Sitemap: https://body3d.bitjian.cn/sitemap.xml`，GSC 通常会自动发现。）
5. **做一次实测（关键验收）**：顶部搜索框输入 `https://body3d.bitjian.cn/` → 回车 → 点「**测试实际网址**」。
   若显示抓取成功、能看到页面内容 → **证明爬虫白名单生效、地域规则没有挡住 Google**。
6. **观察**：左侧「网页」报告看收录数（**单页应用预期只有首页 1 条**）；留意「已发现但未编入索引」属单页应用常见现象。

### 把它当成地域规则的健康监控

> 因为 Google 走海外 IP，**一旦白名单配置出问题，GSC 的「网页」报告会立刻出现抓取错误**。所以接入 GSC 不只是为了收录，它同时是你那套地域拦截规则的**免费监控**。

### 两个细节

- **Search Console 会定期复验**，验证记录 / 放行规则**必须长期保留**，不能"验完就撤"，否则会掉验证状态。
- **收录需要时间**：sitemap 提交后通常 1–2 天开始抓，收录数稳定要几天到几周。
- `BOT_ALLOW` 是 **UA 匹配**，UA 可伪造。这不影响当前（内容是公开的），但**将来上线付费门控时，门控必须走 Cookie 验签，绝不能用 UA 判断**。
