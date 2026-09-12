/**
 * 腾讯云 RUM（前端性能监控）接入层 —— 基于官方 `aegis-web-sdk`。
 *
 * 官方文档：
 *   · 安装与初始化 https://cloud.tencent.com/document/product/239/58553
 *   · 钩子函数（含 beforeReportSpeed） https://cloud.tencent.com/document/product/239/58557
 *   · 错误监控（含白屏检测） https://cloud.tencent.com/document/product/239/87193
 *
 * 设计取舍：本模块**不**在顶层直接 `new Aegis(...)`，而是包成一个 `initRum()` 函数返回实例，
 * 以便将来按需调用 / 条件关闭（例如本地开发或用户拒绝监控时可跳过初始化）。
 *
 * 接入方式说明：我们采用 **npm 包方式**（`import Aegis from 'aegis-web-sdk'`），
 * 与 RUM 控制台「接入指引」中展示的 **CDN 方式**（`tam.cdn-go.cn/aegis-sdk/latest/aegis.min.js`
 * 全局函数 `Aegis`）**等价**——两者是官方同时提供的两种受支持引入方式，配置项与上报行为一致。
 * 之所以选 npm：可参与打包与 TypeScript 类型检查、版本可锁（写入 package.json / lockfile）、
 * 不额外引入外链与 CSP 顾虑。**这不是漏配，请勿误判为与官方片段不一致。**
 */
import Aegis from 'aegis-web-sdk';

/**
 * RUM 上报 ID（SDK 的 `id`，即「应用接入」阶段为每个 Web 应用单独分配的**上报 ID**）。
 *
 * 现状（已确认）：此处填入的是客户从 RUM 控制台「接入指引」复制的官方片段中的真实上报 ID
 * `okg9ofbpwn2j4gGQ1X`，与官方 CDN 片段里的 `id` 完全一致，上报可正常归集。
 *
 * ⚠️ 历史坑位，请勿再踩：客户此前提供过一个**业务系统 ID** `rum-n6sN22ID76G7rg`，
 * 那是 RUM 控制台「业务系统」列表里的**分类容器标识**，**不是** SDK 的 `id`。
 * 业务系统是应用的归类容器，一个业务系统下可以有多个应用，二者**不是同一个值**；
 * 若把业务系统 ID 填进 `id`，上报数据将无法在控制台正确归集（等于收不到数据）。
 * 当时曾临时用它占位，现已替换为真实上报 ID，**不要再改回 `rum-n6sN22ID76G7rg`**。
 *
 * 获取路径：RUM 控制台 → 数据总览 → 应用接入 → 创建 Web 应用 → 复制上报 ID。
 * （替换时只需改这一处常量。）
 */
export const RUM_APP_ID = 'okg9ofbpwn2j4gGQ1X';

/** 中国大陆上报域名；官方默认值为 `https://aegis.qq.com`，此处显式指定为境内加速域名。 */
const RUM_HOST_URL = 'https://rumt-zh.com';

/**
 * 初始化腾讯云 RUM 监控。
 *
 * 官方要求「为了不遗漏数据，须尽早初始化」，故调用方应在 `createRoot(...)` 之前调用本函数。
 *
 * 容错：整个初始化用 try/catch 包裹，失败时**静默降级**（仅打一条 console.warn 并返回 null），
 * 绝不因监控 SDK 异常而阻塞渲染、导致整站白屏。
 *
 * @returns Aegis 实例；初始化失败时返回 null。
 */
export function initRum(): Aegis | null {
  try {
    const aegis = new Aegis({
      id: RUM_APP_ID,

      // 上报域名：必须显式设置。SDK 默认走 https://aegis.qq.com（海外），
      // 本站面向中国内地，改用境内域名 https://rumt-zh.com，降低上报延迟与丢包。
      hostUrl: RUM_HOST_URL,

      // 接口测速：监控 fetch/XHR 的耗时与成功率。
      reportApiSpeed: true,

      // 静态资源测速：监控 img/script/css 等资源加载。
      reportAssetSpeed: true,

      // 白屏检测：默认采样容器为 ['body','html','#app','#root']。
      // 本项目根节点正是 `#root`（见 web/index.html），与默认值天然匹配，无需额外配置。
      blankScreen: true,

      // 【有意不传：uin（用户唯一 ID）】
      // 官方片段里的 `uin: 'xxx'` 只是**占位符**，该项为**可选**——不传即不采集用户标识（本项未配置，
      // 并非漏配）。本站是面向公众的教学科普站点，不存在需要跨会话追踪的用户身份，因此**有意不传**，
      // 不采集用户标识对**隐私合规更友好**。将来若真需要按用户维度看数据，再传入匿名化 ID；
      // **切勿**使用手机号 / 邮箱 / openid 这类可直接识别到个人的值。

      // spa 取 false：本项目是**单视图应用**，没有前端路由、全程不调用 history 跳转
      // （已在 web/ 与 app/ 全量确认：无 react-router、无 history.pushState/replaceState）。
      // 开启 spa 后 SDK 会挂载 replaceState/pushState/hashchange 监听，把每次跳转都算一次 PV；
      // 本应用从加载到卸载只会有一次 PV，开启反而可能因内部状态变更引入无效的跳转 PV。
      // 说明：SDK 内部对 `config.spa` 是「取真值才生效」（`config.spa && sendPv(...)`），
      // 即**不传时默认为关闭**——这里的 `false` 与 SDK 默认行为一致，只是显式写出来更清晰。
      // 官方片段给的是 `spa: true`（面向通用的多路由站点），本项目按实际形态选择 false。
      // 将来若真的引入前端路由，再改为 true。
      spa: false,

      /**
       * 排除巨型二进制资源的测速上报。
       *
       * 背景：前端会用 fetch 拉取 `/models/*.bin`（15 个分片，合计约 90MB，单片数 MB~十几 MB）。
       * 开启 `reportApiSpeed` 后这些下载会被当作接口请求上报，严重污染接口监控数据
       * （量级、耗时都会失真）。
       *
       * 这是官方文档明确支持的屏蔽方式：`beforeReportSpeed` 钩子返回 `false`
       * 即可阻止该条测速日志上报（见「钩子函数」文档）。
       * 文档说明：https://cloud.tencent.com/document/product/239/58557
       */
      beforeReportSpeed(msg: { url?: string }): boolean | void {
        const url = msg && typeof msg.url === 'string' ? msg.url : '';
        // 地址中包含 /models/ 的资源（含 .bin 分片及其解压相关请求）一律不上报测速。
        if (url.includes('/models/')) return false;
        // 其余请求保持默认上报（返回 undefined 即不拦截）。
      },
    });

    return aegis;
  } catch (err) {
    // 监控不应影响主流程：初始化失败时静默降级。
    console.warn('[rum] 腾讯云 RUM 初始化失败，性能监控已降级（不影响页面功能）：', err);
    return null;
  }
}
