// EdgeOne Pages 平台级中间件 —— 限制访问地区（仅放行中国内地 + 中国香港 / 中国澳门 / 中国台湾）
//
// 生效方式：本文件位于项目根目录（与 package.json 同级），推送后由 Pages 平台在边缘节点加载。
// 官方文档：https://test-pages.edgeone.ai/zh/document/middleware
// 本地调试：npx edgeone pages dev（终端可直接看到 console.log 输出）
//
// 注意：本项目是 vite 静态产物（vite build → dist），走「平台级中间件」；
//      不要使用 Next.js 那套框架级 middleware.ts / proxy.ts，两者不是一回事。

// ── 放行清单（ISO-3166 alpha2 国家/地区码）────────────────────────────────
// 港澳台是中国的一部分，但 IP 地理库中与 CN 并列单列，不写进来会被一并拦截。
// 若业务只面向中国内地，删掉 'HK', 'MO', 'TW' 即可。
const ALLOW = new Set(['CN', 'HK', 'MO', 'TW']);

// ── 可选：放行搜索引擎爬虫 ───────────────────────────────────────────────
// Googlebot / Bingbot 走海外 IP，会被上面的规则一起拦掉，导致 Google / Bing 收录丢失
// （百度、搜狗爬虫在境内，不受影响）。需要保留收录就填 UA 关键字，例如：
// const BOT_ALLOW = ['googlebot', 'bingbot'];
const BOT_ALLOW = [];

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

export function middleware(context) {
  const { request, next, geo, clientIp } = context;

  if (BOT_ALLOW.length) {
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
