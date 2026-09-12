#!/usr/bin/env node
/**
 * middleware.js 离线回归测试（不联网、不部署）
 *
 * 为什么需要这个脚本：
 *   1. middleware.js 是 .js，而 tsconfig.json 的 include 只有 .ts/.tsx/.mts，
 *      所以它**不在 `npm run check` 的类型检查范围内**；
 *   2. 本地 `edgeone pages dev` 取不到 geo（会走 FAIL_OPEN 放行），验证不了拦截逻辑；
 *   3. 线上验证要等部署 + 借助海外节点，反馈太慢。
 * 于是这里直接 import 中间件、喂假 context，把全部分支跑一遍。
 *
 * 用法：node scripts/test-middleware.mjs
 * 退出码：0 = 全部通过；1 = 有失败项
 */

import { middleware, config } from '../middleware.js';

let passed = 0;
const failures = [];

function check(name, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) {
    passed += 1;
    console.log(`  PASS  ${name}`);
  } else {
    failures.push({ name, actual, expected });
    console.log(`  FAIL  ${name}  →  实际 ${JSON.stringify(actual)} / 期望 ${JSON.stringify(expected)}`);
  }
}

/** 用假 context 驱动中间件；记录 next() 的调用参数，用于验证「放行时不改动响应头」 */
function run({ country, ua, path = '/' } = {}) {
  const nextCalls = [];
  const next = (...args) => {
    nextCalls.push(args);
    return new Response('OK', { status: 200 });
  };
  const request = new Request(`https://body3d.bitjian.cn${path}`, ua ? { headers: { 'user-agent': ua } } : undefined);

  // 中间件在拦截时会 console.log，这里静音以免刷屏
  const orig = console.log;
  console.log = () => {};
  let res;
  try {
    res = middleware({
      request,
      next,
      geo: country === undefined ? undefined : { countryCodeAlpha2: country },
      clientIp: '203.0.113.7',
    });
  } finally {
    console.log = orig;
  }
  return { status: res.status, nextCalls, res };
}

console.log('\n[1] 放行清单内的地区码 → 期望 200');
for (const c of ['CN', 'HK', 'MO', 'TW']) {
  const { status, nextCalls } = run({ country: c });
  check(`${c} 放行`, status, 200);
  // next() 必须以「零参数」调用 —— 证明我们没有改动任何转发给源站的请求头
  check(`${c} 放行时未改动转发请求头`, nextCalls, [[]]);
}

console.log('\n[2] 小写地区码 → 期望大小写不敏感，同样 200');
check('cn（小写）放行', run({ country: 'cn' }).status, 200);

console.log('\n[3] 海外地区码 → 期望 403');
for (const c of ['US', 'JP', 'SG', 'GB', 'DE', 'KR', 'AU', 'RU']) {
  check(`${c} 拦截`, run({ country: c }).status, 403);
}

console.log('\n[4] 取不到地理位置 → 期望按 FAIL_OPEN 放行（否则本地开发会被自己拦死）');
check('geo 为 undefined 时放行', run({ country: undefined }).status, 200);
check('countryCodeAlpha2 为空串时放行', run({ country: '' }).status, 200);

console.log('\n[5] 拦截响应的形态');
{
  const { res } = run({ country: 'US' });
  const html = await res.text();
  check('状态码 403', res.status, 403);
  check('content-type', res.headers.get('content-type'), 'text/html; charset=utf-8');
  check('cache-control 禁止缓存该 403', res.headers.get('cache-control'), 'no-store, must-revalidate');
  check('正文含中文标题', html.includes('当前地区暂不可访问'), true);
  check('正文含英文说明', html.includes('mainland China only'), true);
}

console.log('\n[6] 模型分块路径放行时不得改动响应头（保护 .bin.gz 的 Content-Encoding 约束）');
{
  const { status, nextCalls } = run({ country: 'CN', path: '/models/body-1.bin.gz' });
  // 本项由 geo ALLOW 规则决定放行，**与 BOT_ALLOW 无关**（UA 为普通浏览器）。
  check('大陆访问分块放行（由 geo 规则决定，不覆盖 BOT_ALLOW）', status, 200);
  check('分块放行时 next() 零参数调用', nextCalls, [[]]);
}

console.log('\n[7] 爬虫白名单（BOT_ALLOW）：放行搜索引擎、恢复 Google / Bing 收录');
const GOOGLEBOT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)';
const BINGBOT = 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)';
const NORMAL_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

// 搜索引擎爬虫从境外 IP 访问首页 → 放行
check('Googlebot（海外 IP）访问 / 放行', run({ country: 'US', ua: GOOGLEBOT }).status, 200);
// 放行时同样不得改动转发给源站的请求头（保护 .bin 的 Content-Encoding 约束）
check('Googlebot 放行时 next() 零参数调用', run({ country: 'US', ua: GOOGLEBOT }).nextCalls, [[]]);
check('Bingbot（海外 IP）访问 / 放行', run({ country: 'US', ua: BINGBOT }).status, 200);
// 普通境外 UA（非白名单爬虫）仍被地域规则拦截
check('普通境外 UA 仍被拦', run({ country: 'US', ua: NORMAL_UA }).status, 403);
// 大陆 UA 完全不受影响
// ⚠️ 下面两项**由 geo ALLOW 规则放行，与 BOT_ALLOW 无关**（大陆 IP 本就通过），改名以消除误导。
check('Googlebot（大陆 IP）放行（由 geo 规则决定，不覆盖 BOT_ALLOW）', run({ country: 'CN', ua: GOOGLEBOT }).status, 200);
check('普通大陆 UA 放行（由 geo 规则决定，不覆盖 BOT_ALLOW）', run({ country: 'CN', ua: NORMAL_UA }).status, 200);

console.log('\n[7a] 爬虫白名单只作用于「地域判断」：受保护前缀 /models/ 不豁免（付费门控预留）');
check(
  'Googlebot 访问 /models/atlas.json 仍被拦',
  run({ country: 'US', ua: GOOGLEBOT, path: '/models/atlas.json' }).status,
  403,
);
check('Bingbot 访问 /models/ 目录本身仍被拦', run({ country: 'US', ua: BINGBOT, path: '/models/' }).status, 403);
check('Googlebot 访问 /models 下深层路径仍被拦', run({ country: 'US', ua: GOOGLEBOT, path: '/models/x/y.bin' }).status, 403);
check('Googlebot 访问带查询串的首页 / 仍放行', run({ country: 'US', ua: GOOGLEBOT, path: '/?q=1' }).status, 200);
// 只是“含 models 字样”的路径不应被误伤（判定要求精确等于 '/models' 或以 '/models/' 开头）
check('Googlebot 访问 /my-models 不受前缀误伤', run({ country: 'US', ua: GOOGLEBOT, path: '/my-models' }).status, 200);

console.log('\n[7b] BOT_ALLOW 清单覆盖：各代表性 UA 从境外 IP 访问 / 均应放行');
const BOT_SAMPLES = {
  'Googlebot 变体(Googlebot-Image)':
    'Mozilla/5.0 (compatible; Googlebot-Image/1.0; +http://www.google.com/bot.html)',
  DuckDuckBot: 'DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)',
  YandexBot: 'Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)',
  Applebot:
    'Mozilla/5.0 (compatible; Applebot/0.1; +http://www.apple.com/go/applebot)',
  PetalBot: 'Mozilla/5.0 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)',
  Twitterbot: 'Twitterbot/1.0',
  facebookexternalhit: 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
  TelegramBot: 'TelegramBot (like TwitterBot)',
  Discordbot: 'Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)',
  Slackbot: 'Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)',
  LinkedInBot: 'Mozilla/5.0 (compatible; LinkedInBot/1.0; +http://www.linkedin.com)',
  'Chrome-Lighthouse':
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Chrome-Lighthouse',
  GTmetrix:
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 GTmetrix',
  Pingdom: 'Pingdom.com_bot_version_1.4 (http://www.pingdom.com/)',
};
for (const [name, ua] of Object.entries(BOT_SAMPLES)) {
  check(`${name} 从境外 IP 放行`, run({ country: 'US', ua }).status, 200);
}

console.log('\n[7c] 境内爬虫刻意**不放入**白名单（避免扩大 UA 伪造绕过面）');
const DOMESTIC_BOTS = {
  Baiduspider: 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
  'Sogou spider': 'Sogou web spider/4.0(+http://www.sogou.com/docs/help/webmasters.htm#07)',
  '360Spider': 'Mozilla/5.0 (compatible; 360Spider; http://www.so.com/help/help_3_2.html)',
  Bytespider: 'Mozilla/5.0 (compatible; Bytespider; https://zhanzhang.toutiao.com/)',
};
for (const [name, ua] of Object.entries(DOMESTIC_BOTS)) {
  // 海外 IP 伪装成境内爬虫 → 仍应被拦（证明其未进白名单）
  check(`${name}（境外 IP）仍被拦`, run({ country: 'US', ua }).status, 403);
  // 大陆 IP → 由地域规则正常放行（与是否在白名单无关，本项不覆盖 BOT_ALLOW）
  check(`${name}（大陆 IP）放行（由 geo 规则决定，不覆盖 BOT_ALLOW）`, run({ country: 'CN', ua }).status, 200);
}

console.log('\n[7d] 收录功能验收线：Googlebot + 境外 IP 抓 /robots.txt 与 /sitemap.xml 必须 200');
// 这两条是「恢复 Google / Bing 收录」的功能验收线——robots/sitemap 若被 403，收录目标即不成立。
check('Googlebot 抓 /robots.txt 放行', run({ country: 'US', ua: GOOGLEBOT, path: '/robots.txt' }).status, 200);
check('Googlebot 抓 /sitemap.xml 放行', run({ country: 'US', ua: GOOGLEBOT, path: '/sitemap.xml' }).status, 200);
check('Bingbot 抓 /sitemap.xml 放行', run({ country: 'US', ua: BINGBOT, path: '/sitemap.xml' }).status, 200);
// 反向校验：白名单之外的普通境外 UA 抓 robots.txt 仍被地域规则拦（证明放行确由白名单带来）
check('普通境外 UA 抓 /robots.txt 仍被拦', run({ country: 'US', ua: NORMAL_UA, path: '/robots.txt' }).status, 403);

console.log('\n[7f] Google Search Console 抓取器（UA 不含 googlebot 子串，必须单列白名单）');
// ⚠️ 关键点：这两个 UA 里**不含** 'googlebot'，靠 'googlebot' 兜不住，必须单独列进 BOT_ALLOW，
//    否则 GSC 属性验证 / 网址检查会因海外抓取源被地域规则 403 而**必然失败**。
const GSC_VERIFY_UA = 'Mozilla/5.0 (compatible; Google-Site-Verification/1.0)';
const GSC_INSPECT_UA = 'Google-InspectionTool';

// 期望放行（境外 IP + GSC 抓取器 UA → 200）
check('GSC 属性验证抓取器（海外 IP）抓首页 / 放行（meta 标签验证路径）', run({ country: 'US', ua: GSC_VERIFY_UA }).status, 200);
check(
  'GSC 属性验证抓取器（海外 IP）抓根路径验证文件放行',
  run({ country: 'US', ua: GSC_VERIFY_UA, path: '/google1a2b3c4d.html' }).status,
  200,
);
check('GSC 属性验证抓取器（海外 IP）抓 /robots.txt 放行', run({ country: 'US', ua: GSC_VERIFY_UA, path: '/robots.txt' }).status, 200);
check('GSC 属性验证抓取器（海外 IP）抓 /sitemap.xml 放行', run({ country: 'US', ua: GSC_VERIFY_UA, path: '/sitemap.xml' }).status, 200);
check('GSC 网址检查工具（海外 IP）抓首页 / 放行', run({ country: 'US', ua: GSC_INSPECT_UA }).status, 200);
// 放行时同样不得改动转发给源站的请求头（保护 .bin 的 Content-Encoding 约束）
check('GSC 属性验证抓取器放行时 next() 零参数调用', run({ country: 'US', ua: GSC_VERIFY_UA }).nextCalls, [[]]);

// 期望拦截（境外 IP + GSC 抓取器 UA → 403，gated 生效）：与 googlebot 走同一条判定
check('GSC 属性验证抓取器抓 /models/atlas.json 仍被拦（gated 生效）', run({ country: 'US', ua: GSC_VERIFY_UA, path: '/models/atlas.json' }).status, 403);
check('GSC 网址检查工具抓 /models/atlas.json 仍被拦（gated 生效）', run({ country: 'US', ua: GSC_INSPECT_UA, path: '/models/atlas.json' }).status, 403);

// 反向不误伤：普通浏览器 UA 从境外 IP 抓 / 仍被地域规则拦（证明放行确由白名单带来）
check('普通境外 UA 抓 / 仍被拦（地域规则生效）', run({ country: 'US', ua: NORMAL_UA }).status, 403);

console.log('\n[7e] 规范化主回归：平台**会路由到真实文件**的写法，必须全部判为 gated（403）');
// 依据真实部署实测：平台会折叠连续斜杠 / 折叠点段 / 把 '\' 当 '/' / 解码 '%2e'。
const GATED_ROUTABLE = [
  '/models/atlas.json', // 基准
  '//models/atlas.json', // 连续斜杠（平台会折叠）
  '/\\models/atlas.json', // '\' 当 '/'（新实证）
  '/models\\atlas.json', // '\' 当 '/'（新实证）
  '/./models/atlas.json', // 点段折叠
  '/models/../models/atlas.json', // 点段折叠
  '/%2e/models/atlas.json', // 平台会解码 %2e（新实证）
];
for (const path of GATED_ROUTABLE) {
  check(`Googlebot 访问 ${path} 判为 gated 仍被拦`, run({ country: 'US', ua: GOOGLEBOT, path }).status, 403);
}

console.log('\n[7e-2] 其它变体 / 纵深防御层：同样必须 403');
const GATED_VARIANTS = [
  '/MODELS/atlas.json', // 大小写绕过
  // 线上平台**不**解码 %2F / %5C（这两类请求落到 index.html 兜底、拿不到真实文件），
  // 故下列两项属纵深防御，非可利用漏洞；修 normalizePath 步骤顺序后仍应判为 gated。
  '/models%2Fatlas.json', // %2F 百分号编码
  '/%5Cmodels/atlas.json', // %5C 编码反斜杠（曾因步骤顺序缺陷被判为非 gated，本项为回归）
  '/%6Dodels/atlas.json', // %6D -> m 编码
  '/foo%2F..%2Fmodels/x', // 编码斜杠展开出点段（纵深防御：靠「先解码、后折点段」的顺序封堵）
  '/models', // 精确等于前缀（无尾斜杠）
  '/models/', // 前缀 + 斜杠
  '/models/x/y.bin', // 深层路径
  '/models?q=1', // 带查询串，路径仍为 /models
];
for (const path of GATED_VARIANTS) {
  check(`Googlebot 访问 ${path} 判为 gated 仍被拦`, run({ country: 'US', ua: GOOGLEBOT, path }).status, 403);
}

console.log('\n[7e-3] 反例（防误伤）：不应被 gated 的路径应保持 200');
check('Googlebot 访问 /modelsomething/x 放行（不误伤）', run({ country: 'US', ua: GOOGLEBOT, path: '/modelsomething/x' }).status, 200);
check('Googlebot 访问 /my-models 放行（不误伤）', run({ country: 'US', ua: GOOGLEBOT, path: '/my-models' }).status, 200);
// 本判定只保护站点根路径下的 /models/（真实模型分片只在根路径提供）；/foo/models/x 不存在、不暴露资源，故不门控。
check(
  'Googlebot 访问 /foo/models/x 放行（本判定只保护根路径下的 /models/，见 middleware.js 注释）',
  run({ country: 'US', ua: GOOGLEBOT, path: '/foo/models/x' }).status,
  200,
);

console.log('\n[8] 路由匹配配置');
check('matcher', config.matcher, ['/:path*']);

console.log(`\n${'─'.repeat(56)}`);
if (failures.length) {
  console.log(`结果：${passed} 通过 / ${failures.length} 失败`);
  for (const f of failures) console.log(`  · ${f.name}`);
  process.exit(1);
}
console.log(`结果：全部通过（${passed} 项断言）`);
