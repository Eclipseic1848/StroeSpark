# StoreSpark 前端验证记录

日期：2026-10-28。当前前端为 React、TypeScript 和 Vite，未接入真实模型密钥。

## 实际通过的检查

- `npm run build`：TypeScript 与 Vite production build 通过，输出为 `web/dist/`。
- `npm test`：5 项 Playwright 测试通过。覆盖任务创建、素材上传与失败重试、模型失败保留输入、不显示虚假成功、文案编辑、未保存导航保护、导出、401 连接恢复、密钥默认隐藏及不持久保存、390px 窄屏和减少动态效果。
- 编辑回归包含标题前后空白及正文末尾换行。保存成功后，以服务端返回的实际内容重置编辑值，恢复已保存状态及导出；失败不覆盖输入。
- `python <frontend-design-premium技能目录>/scripts/audit_project.py <项目根目录> --mode strict --config web/premium-ui.json --output web/design/premium-audit.json`：0 问题。
- `npx -p @google/design.md designmd lint ../DESIGN.md`：0 errors；7 条组件未显式引用颜色 token 的提示。实际颜色由全局 CSS 变量统一消费，未将提示解释为运行错误。
- 新锁文件包含 Rolldown 的 Windows、Linux GNU、Linux Musl 原生包，以及 20 个 Linux 专用条目。与旧锁中共有的包相比，版本无变化；本机未执行 Linux 构建。

上述 5 项 Playwright 测试通过 `page.route` 隔离 API，测试回复明确为合成内容。

另在主线程启动 `tests/runtime_server.py --data-dir test-results/integration-api --port 8000` 后，实际执行 `node scripts/integration-smoke.mjs`，不拦截任何 API 请求。该轮通过真实 FastAPI 与 SQLite 完成新建“浏览器联调测试”、上传 UTF-8 TXT、提出方向、生成、人工编辑并核对首尾空白归一化、Markdown 导出、模型 fixture 返回 502 后保留输入及已有文案，以及 390px 无水平溢出。结果见 [integration-result.json](integration-result.json)。JavaScript 运行错误为 0；控制台仅出现预期的模型 502 资源错误。

此联调服务只有模型传输使用 MockTransport，没有真实模型费用或商家数据。脚本只供该测试服务的手动联调，未加入默认 `npm test`，CI 不依赖人工启动服务。它不证明 DeepSeek 调用或商家任务已经通过。

当前没有 Browser/IAB 工具，使用安装的 Playwright Chromium 156 浏览器。原生视口为 1504×1048，窄屏为 390×844。已通过 `view_image` 同轮查看概念图、桌面空态、任务编辑页和窄屏截图，以及真实 API 联调截图。

## 视觉核对

| 项目 | 概念基准 | 实际实现及结论 |
|---|---|---|
| 颜色 | 纯白、深青主操作、橙色小标记 | 颜色来自 `styles.css` 语义变量，未改成米白或加入背景图片。 |
| 布局 | 左侧任务、右侧表单与交付说明 | 保留三部分关系；任务详情在同一界面将沟通与内容并列。 |
| 标题和操作 | 从一个宣传想法开始、新建任务、创建任务、模型设置 | 主标题与关键操作一致，没有加入营销标签、假指标或示例任务。 |
| 文字层级 | 标题明显、标签清楚、辅助文字较轻 | 控件与内容字体均显式设置；长任务名和正文允许换行。 |
| 组件 | 细边界、适度圆角、安静的工作台 | 按钮、字段、消息反馈与焦点状态共用样式；无重复卡片网格。 |
| 移动端 | 同一任务关系需可继续使用 | 侧栏移到顶部，表单与内容变为单列；390px 未出现水平溢出，核心动作仍可见。 |

## 有意保留的设计差异

概念由助手生成作为实现基准，尚未经过商家视觉验收。以下差异由已确认的使用要求与实际 API 决定：

- 侧栏采用 248px，给常见笔记本宽度保留编辑空间；概念图侧栏更宽。
- 渠道与形式采用自由文本输入，并在桌面并排；首版尚无已确认的完整渠道选项，不制造下拉清单。
- 新建任务增加真实文件选择，允许仅提供素材开始；任务名称可省略，由已有输入生成标题。
- 内容交付明确为首版宣传文案，不暗示已经支持海报渲染或视频成片。
- 省略空态文件插画及设置齿轮图标，用清楚的文字动作承载相同功能。

上述差异已逐项检查；当前截图没有发现文字裁切、控件重叠、乱码或不可达的主操作。页面未按“像素完全相同”或“商家已验收”对外宣称。

## 安装恢复记录

暂停安装留下的 Rolldown `.node` 文件仅 3,539,648 字节，PE 节表要求至少 21,731,328 字节，证实文件被截断。原包保留为 `web/node_modules/@rolldown/.binding-win32-x64-msvc-interrupted-20261028/`，只定点恢复该包，随后构建通过。

原有 Windows 锁文件保留于 `web/node_modules/.storespark-lock-generation/package-lock.before-multiplatform.json`。在独立无安装目录的环境中生成完整跨平台 lock，再复制到 `web/package-lock.json`，未清理原安装现场。

真实 API 首轮检查另发现 Vite 的字符串代理简写改变 Host，触发同源校验 403。改为显式 `target` 与 `changeOrigin: false` 后联调通过，没有放宽后端同源保护。缺失 favicon 的浏览器 404 已通过与原标记一致的 SVG 图标修复。

## 未验证范围

本记录的本地浏览器环境为 Windows/Chromium；Linux 构建与浏览器交互后续已由主线程通过 GitHub CI 核验，见根目录 handoff.md。Safari、Firefox、手机真机、微信小程序、真实 DeepSeek 成本与输出、模型中断后的服务器重启恢复或多人并发编辑仍未验证。当前浏览器隔离测试不代替这些检查。
