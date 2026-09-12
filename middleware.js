// EdgeOne Pages 平台级中间件 —— 限制访问地区（仅放行中国内地 + 中国香港 / 中国澳门 / 中国台湾）
//
// 生效方式：本文件位于项目根目录（与 package.json 同级），推送后由 Pages 平台在边缘节点加载。
// 官方文档：https://test-pages.edgeone.ai/zh/document/middleware
// 本地调试：npx edgeone pages dev（终端可直接看到 console.log 输出）
//
// 注意：本项目是 vite 静态产物（vite build → dist），走「平台级中间件」；
//      不要使用 Next.js 那套框架级 middleware.ts / proxy.ts，两者不是一回事。
//
// ⚠️ 安全说明（重要）：
//   User-Agent **完全可被客户端伪造**，因此下面的 BOT_ALLOW 只是「让搜索引擎能正常收录」
//   的便利清单，**它不是安全机制**。任何伪造 UA 的境外访问仍然能进入本站
//   （本站内容免费，此风险目前可接受）。一旦将来上线「兑换码付费门控」，
//   门控**必须走 Cookie 验签 / 服务端权益校验**，绝不能再依赖 UA 判断——
//   否则伪造一个 Googlebot UA 就能白嫖付费内容。

// ── 放行清单（ISO-3166 alpha2 国家/地区码）────────────────────────────────
// 港澳台是中国的一部分，但 IP 地理库中与 CN 并列单列，不写进来会被一并拦截。
// 若业务只面向中国内地，删掉 'HK', 'MO', 'TW' 即可。
const ALLOW = new Set(['CN', 'HK', 'MO', 'TW']);

// ── 放行搜索引擎爬虫（按 UA 关键字小写匹配）──────────────────────────────
// 背景：Googlebot / Bingbot 等走海外 IP，会被上面的地域规则一起拦掉，
//      导致 Google / Bing 完全无法收录本站。填在此处的爬虫即使来自海外 IP 也放行。
//
// 为什么**不放**百度 / 搜狗 / 360 / 字节等境内爬虫（baiduspider、sogou、360spider、bytespider…）：
//   它们本身就在境内，早已被上面的地域规则正常放行，放进白名单没有任何收益，
//   反而会平白扩大「UA 伪造绕过」的攻击面（海外请求只要伪装成这些 UA 就能进来）。
//
// 为什么爬虫白名单**只作用于地域判断**、不作用于权益判断：
//   见下方 GATED_PREFIXES 注释。
const BOT_ALLOW = [
  // ── 国际搜索引擎 ────────────────────────────────────────────────────────
  'googlebot', // Google 网页/图片/视频/新闻爬虫（变体 UA 均含该串，如 Googlebot-Image）
  'bingbot', // Microsoft Bing 爬虫
  'duckduckbot', // DuckDuckGo 爬虫
  'yandexbot', // Yandex（俄罗斯）爬虫
  'applebot', // Apple（Siri / Spotlight）爬虫
  'petalbot', // 华为花瓣搜索爬虫（走海外 IP）
  // ── Google Search Console（GSC）─────────────────────────────────────────
  // 为什么必须**单列**、不能靠上面的 'googlebot' 兜住：这两个 UA 的字符串里**不含**
  //   'googlebot' 子串，若不加进来就会落到地域规则（抓取源在海外 → 被 403），
  //   导致 Search Console 的属性验证 / 网址检查**必然失败**。
  'google-site-verification', // GSC 属性所有权验证抓取器（UA: Mozilla/5.0 (compatible; Google-Site-Verification/1.0)）。
  //                            它会抓**根路径的验证文件**（形如 /google1a2b3c4d.html）或**首页**（meta 标签验证方式）；
  //                            抓取源在美国，故需走白名单跳过地域拦截。
  'google-inspectiontool', // GSC「网址检查 / 测试实际网址」工具抓取器（UA: Google-InspectionTool）。
  //                          客户排查「Google 到底能不能抓到我的页面」时用它；抓取源同样在海外。
  // 注意：GSC 验证文件与首页都在受保护前缀 /models/ **之外**，不需要也不应该放开 /models/——
  //       这两个 UA 与 googlebot 走同一条 isGatedPath 判定，落在 /models/* 下仍照常返回 403。
  // ── 链接预览 / 社交卡片（决定分享链接能否正确生成缩略图与摘要）──────────
  'twitterbot', // X / Twitter 卡片抓取
  'facebookexternalhit', // Facebook / Meta 链接预览
  'telegrambot', // Telegram 链接预览
  'discordbot', // Discord 链接嵌入
  'slackbot', // Slack 链接展开
  'linkedinbot', // LinkedIn 链接预览
  // ── 站点质量与性能检测 ──────────────────────────────────────────────────
  'chrome-lighthouse', // Chrome Lighthouse（含 PageSpeed Insights）审计
  'lighthouse', // Lighthouse 通用 UA（覆盖未带 chrome- 前缀的变体）
  'gtmetrix', // GTmetrix 性能测试
  'pingdom', // Pingdom 站点可用性监控
];

// ── 受保护路径前缀（为「兑换码付费门控」预留）────────────────────────────
// 爬虫白名单**只在路径不在此前缀内时才生效**。
// 原因：付费门控一旦上线，若爬虫白名单是「无条件放行」，Googlebot 就会成为付费内容的
//      免费后门——任何人伪装成 Googlebot 即可绕过付费墙。所以爬虫白名单**永远只能作用于
//      地域判断，绝不能作用于权益判断**。
// 当前本站没有门控、内容免费，因此此常量不对任何真实流量产生影响，纯粹是为未来预留。
//
// ⚠️ 这里**故意不带尾斜杠**，命中判定由 isGatedPath() 完成：
//    「路径规范化后**精确等于** '/models'」或「**以 '/models/' 开头**」才算命中。
//    · 绝不能退化成 startsWith('/models')：否则 '/modelsomething/x' 会被误判（误伤）。
//    · 判定前先做规范化（见 normalizePath），以封堵 %2F 编码 / 大小写 / 连续斜杠 / 点段 等绕过。
//    · **本判定只保护站点根路径下的 /models/**（真实的 15 个 .bin 分片只在根路径下提供）。
//      像 '/foo/models/x' 这种中间层级路径**不**受保护——它在真实站点上不存在（origin 返回 404），
//      不暴露任何真实资源，因此不纳入门控，避免过度拦截。此语义边界在此明确声明。
const GATED_PREFIXES = ['/models'];

// ── 取不到地理位置时的兜底 ───────────────────────────────────────────────
// true  = 放行（保可用性，本地 dev 与个别查不到归属的 IP 不会被误伤）
// false = 拦截（保严格性）
const FAIL_OPEN = true;

const BLOCK_HTML = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">
<title>当前地区暂不可访问</title>
<style>
html,body{height:100%}
body{margin:0;display:flex;align-items:center;justify-content:center;padding:24px;background:#f3f4f4;color:#20242b;font-family:'Helvetica Neue',Arial,'PingFang SC',sans-serif;-webkit-font-smoothing:antialiased}
.card{width:100%;max-width:30rem;background:#fff;border:1px solid #25384a17;border-radius:12px;padding:32px 28px;box-shadow:0 16px 48px #2433440a}
.eyebrow{display:flex;align-items:center;gap:8px;font-size:12px;letter-spacing:.19em;color:#737d89;text-transform:uppercase}
.dot{width:5px;height:5px;border-radius:50%;background:#a8574a;box-shadow:0 0 12px #a8574a26}
h1{margin:14px 0 12px;font-size:22px;font-weight:400;letter-spacing:-.4px;line-height:1.35}
p{margin:0;font-size:13px;line-height:1.75;color:#68727d}
p.en{margin-top:10px;color:#8a939c}
.foot{margin-top:24px;padding-top:14px;border-top:1px solid #25384a17;display:flex;justify-content:space-between;font-size:12px;color:#9aa3ab;letter-spacing:.02em}
</style>
</head>
<body>
<div class="card">
<div class="eyebrow"><span class="dot"></span>Access restricted</div>
<h1>当前地区暂不可访问</h1>
<p>本站目前仅面向中国内地用户开放。请切换到中国内地网络环境后重试。</p>
<p class="en">This site is currently available in mainland China only. Please try again from a mainland China network.</p>
<div class="foot"><span>HTTP 403</span><span>EdgeOne Pages</span></div>
</div>
</body>
</html>`;

function blocked(reason, clientIp) {
  console.log(`[geo-block] ${reason} ip=${clientIp || '-'} -> 403`);
  return new Response(BLOCK_HTML, {
    status: 403,
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': 'no-store, must-revalidate',
    },
  });
}

/**
 * 规范化请求路径，**仅用于受保护前缀判定**（绝不用于改写转发给源站的请求）。
 *
 * 逐步封堵以下绕过手法（步骤 1-6，**顺序不可随意调换**）：
 *   1) 百分号解码：如 '/models%2Fatlas.json'——若不先解码，'%2F' 看起来只是普通字符，
 *      会被误判为「不在受保护前缀内」从而触发爬虫白名单。故先 decodeURIComponent。
 *      ⚠️ 必须 try/catch 兜住非法百分号编码（如裸 '%'）：解码失败时退回原串，绝不让中间件抛异常。
 *   2) 统一小写：防 '/MODELS/...' 大小写绕过。
 *   3) 反斜杠归一为斜杠：平台把 '\' 当 '/'（实测：'/%5Cmodels/x' 解码后得 '/\models/x' 也应命中）。
 *      ⚠️ **必须在第 5 步「URL 重解析」之前做**：否则 URL 解析会把 '\' 规范化为 '/' 并可能产生前导 '//'，
 *         而相对 URL 语境下 '//xxx' 会被当成「协议相对 URL」，把 xxx 误当 authority(host)、**丢弃路径**
 *         （实测 'new URL("/\\models/atlas.json", base).pathname' 得到 '/atlas.json'，models 段整段丢失）。
 *   4) 折叠连续斜杠：如 '//models/...'——WHATWG URL 只折叠 '.'/'..'，**不会**折叠连续斜杠，故手动折叠。
 *   5) 折叠点段：解码后可能新增 '.'/'..' 段（如 '/foo%2F..%2Fmodels' 解码为 '/foo/../models'），
 *      再用 URL 解析折掉。此时前导必为单个 '/'，不会触发第 3 步描述的「协议相对 URL」误判。
 *   6) 末尾再折一次连续斜杠（幂等）：消除「折叠步骤被后续步骤重新破坏」这一整类 bug。
 *
 * ── 平台路由实测语义（硬证据，注释以此为准）──────────────────────────────
 * 本判定是**纵深防御层**，需与线上平台真实路由行为对齐。经真实部署实测：
 *   · 平台**会**折叠连续斜杠、折叠点段、**把 '\' 当 '/'**、**会**解码 '%2e'；
 *     因此以下写法都能命中真实文件，**都必须**判为 gated：
 *       /models/atlas.json、//models/atlas.json、/\models/atlas.json、/models\atlas.json、
 *       /./models/atlas.json、/models/../models/atlas.json、/%2e/models/atlas.json
 *   · 平台**不**解码编码后的斜杠 / 反斜杠（'%2F'、'%5C'）：这类请求会落到 index.html 兜底、
 *     线上**拿不到**真实文件，故 '/models%2Fatlas.json'、'/%5Cmodels/atlas.json' 属纵深防御、非可利用漏洞。
 *   · 大小写不匹配 / 不存在的路径（/MODELS/…、/models、/foo/models/…、/modelsomething/x）平台不路由到真实文件。
 *
 * @param {string} requestUrl 完整的请求 URL（如 https://body3d.bitjian.cn/models/atlas.json）
 * @returns {string} 规范化后的路径（始终以 '/' 开头）
 */
function normalizePath(requestUrl) {
  let pathname = '/';
  try {
    pathname = new URL(requestUrl).pathname;
  } catch {
    // 非法 URL：保守回退为根路径，避免抛异常影响中间件。
    return '/';
  }

  // 1) 百分号解码：防 %2F / %5C / %6D 等编码绕过；非法编码时退回原串（不抛错）。
  try {
    pathname = decodeURIComponent(pathname);
  } catch {
    // 保留原串继续后续规范化。
  }

  // 2) 统一小写：防 /MODELS/ 大小写绕过。
  pathname = pathname.toLowerCase();

  // 3) 反斜杠归一为斜杠：平台把 '\' 当 '/'。必须在第 5 步 URL 重解析之前做，
  //    否则 '\' 会被解析成 '/' 并可能生成前导 '//'，触发「协议相对 URL」误判、丢失路径段。
  pathname = pathname.replace(/\\/g, '/');

  // 4) 折叠连续斜杠：防 //models/ 绕过。
  pathname = pathname.replace(/\/{2,}/g, '/');

  // 5) 折叠点段：防 /%2e/models、/foo/../models、/foo%2F..%2Fmodels 绕过。
  try {
    pathname = new URL(pathname, 'https://normalize.invalid/').pathname;
  } catch {
    // 理论上不会走到；保守保留当前值。
  }

  // 6) 末尾再折叠一次连续斜杠（幂等）：确保任何前序步骤都不残留 '//'。
  pathname = pathname.replace(/\/{2,}/g, '/');

  return pathname;
}

/**
 * 判断路径是否落在受保护前缀内（规范化后判定）。
 * 命中条件：**精确等于前缀**，或**以「前缀 + '/'」开头**。
 * 之所以不写成 startsWith(prefix)，是为避免 '/modelsomething/x' 被误判为受保护。
 *
 * @param {string} requestUrl 完整请求 URL
 * @returns {boolean} 是否受保护（受保护则爬虫白名单不生效）
 */
function isGatedPath(requestUrl) {
  const pathname = normalizePath(requestUrl);
  return GATED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function middleware(context) {
  const { request, next, geo, clientIp } = context;

  // 爬虫白名单：仅作用于「地域判断」。路径落在 GATED_PREFIXES 内时跳过白名单，
  // 让后续的地域规则（以及未来的权益规则）照常裁决。
  // 注意：规范化后的路径只用于此处判定，next() 仍以零参数调用，绝不改写转发请求/响应头。
  if (BOT_ALLOW.length && !isGatedPath(request.url)) {
    const ua = (request.headers.get('user-agent') || '').toLowerCase();
    if (BOT_ALLOW.some((bot) => ua.includes(bot))) return next();
  }

  const code = (geo && geo.countryCodeAlpha2 ? geo.countryCodeAlpha2 : '').toUpperCase();

  if (!code) return FAIL_OPEN ? next() : blocked('geo-unknown', clientIp);
  if (ALLOW.has(code)) return next();

  return blocked(`region=${code}`, clientIp);
}

// 默认匹配所有路由，显式写出来便于以后只拦部分路径
export const config = { matcher: ['/:path*'] };
