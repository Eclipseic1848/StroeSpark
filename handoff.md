# StoreSpark 项目交接

更新日期：2026-10-28。

## 当前状态

- 项目根目录为 F:/new branch/StoreSpark。
- 用户已于 2026-10-28 明确要求继续，原暂停已解除；Windows 开发、未来 Linux 部署和可能的小程序客户端要求继续有效。
- 用户已提供并授权同步 [Eclipseic1848/StroeSpark](https://github.com/Eclipseic1848/StroeSpark)，要求创建并执行相关 Issues。origin 已关联，实现提交 `84e4e0cf60dcbec4084d7e027737ead420d7a0f6` 已推送 main；保留远端初始化历史，未强制覆盖。后续有验收文档提交，精确 HEAD 以当前 Git 为准。
- 当前采用 Python FastAPI + SQLite、React + TypeScript + Vite。首版 Web 工作台已补齐，生产构建、5 项 Chromium 交互及实际 API 浏览器联调通过；远端 Windows/Linux 后端、Web 与 Linux 容器 CI 四项全部成功，尚未作商家或生产验收。
- 用户要求借鉴 Mangrove 的 provider 配置，并提供官方直连 DeepSeek Flash；默认 `https://api.deepseek.com`、`deepseek-flash`。已实现单配置加密保存与服务端调用，未接入真实密钥或验证真实请求。
- 上传限额已修复为解析前限制，非法 IDNA 地址与非 ASCII 授权头两个边界错误也已修复；目前后端 46 项检查通过，含实际 TCP 进程、重启和并发检查。
- 已创建并执行 GitHub #1 至 #5。#1、#2、#3、#5 已验收关闭，#4 真实模型与商家验证需要外部资料，保持开放。详见[GitHub 任务跟踪](docs/github-tracking.md)。
- 英文项目工作名 StoreSpark；中文名店有招和宣传语由助手建议，尚未最终确认或查重。

## 阅读入口

1. [README.md](README.md)：项目总览和文档导航。
2. [AGENTS.md](AGENTS.md)：本项目工作约定。
3. [产品定义初稿](docs/product-definition.md)：当前定义及未定边界。
4. [需求与决策记录](docs/discovery-log.md)：用户反馈、明确要求和验证问题。
5. [产品流程草案](docs/product-flow-draft.md)：本轮新增，说明每一步的输入、系统动作和交付结果，区分已确认要求与流程建议。
6. [开发暂停记录](docs/development-checkpoint.md)：此前暂停时的历史现场，当前状态以本交接和 GitHub 跟踪为准。
7. [开发与部署](docs/development-and-deployment.md)：Windows 运行、模型配置、Linux 容器、迁移和备份。
8. [GitHub 任务跟踪](docs/github-tracking.md)：本轮 Issues、验收边界和执行状态。

另有[内容制作 Skills 和模板调研](docs/research/content-skills-landscape-2026-10-26.md)，在本轮整理期间新增。本轮仅补充入口，未修改原文、复核外部结论或采用其中的工具建议。

## 不应遗漏的用户要求

优先餐饮，后续考虑快消。服务店主、门店及品牌运营人员，目标是让消费者愿意进店尝试。

需求清楚和模糊两种情况都要支持；素材充足和零准备两种情况也都要支持。技术小白可以通过追问逐步收敛；已有菜单、照片或其他宣传素材的用户，应有地方提交并用于任务。

用户认可的交付组合是宣传方向、对应成品，以及使用和验证建议。多场景、多格式是方向要求，但未确定首版渠道和格式清单。

## 证据与待定边界

真实需求例子为东北蒸饺在南方或江苏开店。商家未直接说明具体困难，发起人表示他们在用多种 AI 工具，但对产出质量、美观度和吸引力不满意。目前没有原始访谈、实际素材或到店效果数据。

不能把内容不满意直接归因为缺少消费者洞察，也不能把商家觉得好看视为消费者愿意进店。公开互联网信息能提供什么依据、哪些来源可访问，以及分析结果是否有效，均未验证。

自动发布、广告投放和代运营不纳入首版，只是助手提出的建议，尚未获得单独确认。收费模式、质量标准、首版范围、投入时间、技术方案及名称查重也未定。

## 接续工作的优先事项

1. 当前已恢复开发。先核对本地文件和 Git 状态，保留已有工作；GitHub 推送和 Issue 操作已获用户明确授权，不能覆盖远端新增未知工作。
2. 在当前定义上继续产品讨论；每轮最多追问 1 至 3 个关键问题，避免反复要求用户在已明确兼容的两种情况中二选一。
3. 用户已澄清自己是 IT 实现人员，无法代商家提供准确的业务答案。商家细节记为待验证，不要求用户扮演店主补齐；助手可先提出标注假设的产品流程供讨论，不替商家补造事实，也不将流程草案当作已确认的开发范围。
4. 本轮工程已完成并推送，后续以 #4 为优先：请用户在本机模型设置或服务端 `.env` 安全配置 DeepSeek 密钥，再进行实际模型调用。不要要求用户在聊天或 Issue 粘贴密钥，不读取 Mangrove 凭据。
5. 在真实模型可用后，验证输出结构、失败恢复及素材理解，并结合可获得的商家实际任务继续收敛质量标准和首版渠道。当前仅支持文本与 Markdown，未实现海报渲染、视频成片、联网调研、小程序客户端或多租户；相关扩展仍需按新任务确定范围。

## 本轮验证范围

Windows Python 3.14.6 后端 46 项检查通过；包含隔离模型、真实 TCP 服务进程、重启读取、同任务并发、上传请求体边界及配置/鉴权输入检查。Web 生产构建和 5 项 Chromium 隔离 API 交互检查通过，跨平台 lock 已核对 Linux 原生依赖条目。Compose 配置解析通过；本机 Docker Linux Engine 未运行，容器实测已在 GitHub CI 完成。

[CI Run 40800541934](https://github.com/Eclipseic1848/StroeSpark/actions/runs/40800541934) 对实现提交 `84e4e0c` 的 Windows 后端、Linux 后端、Web 构建与交互、Linux 容器启动与持久化四项作业均成功，逐项步骤亦已核验。容器检查覆盖非 root 用户、静态页面、令牌、任务保存、无模型密钥时诚实失败和重启后读取。

实际 FastAPI + SQLite 浏览器联调未拦截业务 API，完成新建、UTF-8 素材、方向、生成、人工编辑、导出、失败保留输入及 390px 检查，浏览器运行错误为 0。模型仅用明确的测试 fixture，不计作真实 DeepSeek 请求。联调还发现并修复 Vite 代理 Host 问题，现显式 `changeOrigin:false`，保留后端同源保护。记录见 `web/design/verification.md` 和 `web/design/integration-result.json`。

联调 fixture 已停止；正常服务在本机 `http://127.0.0.1:8000` 托管构建后的 Web，模型未配置，数据目录为默认 `data`。未发布到外部环境。

## 内容制作 Skill 与模板调研归档

归档日期：2026-10-26。用户指定本目录保存项目重要信息，作为未来项目仓库。已保留现有产品定义、需求记录和协作约定，新增[内容制作 Skill 与模板调研](docs/research/content-skills-landscape-2026-10-26.md)，并在 README 中建立入口。

调研覆盖品牌、快消、零售及餐饮，包含 13 个 GitHub 项目的具体 Skill、模板链接、适用场景、依赖与能力边界，以及许可证、热度和维护状态快照。内容基于上游 README、SKILL.md、模板及相关脚本的只读核验；行业适配属于分析，未经过实际品牌任务或投放验证。

- 品牌口径及广告创意：优先研究 coreyhaines31/marketingskills。
- 中文连续图文、封面和信息图：优先研究 JimLiu/baoyu-skills。
- 零售商品详情及品类内容：研究 writer/skills 的 pdp-content 和 nexscope-ai/eCommerce-Skills。
- 餐饮内容月历、广告文案和拍摄 brief：研究 zubair-trabzada/ai-restaurant-claude；miron-tech 的模板可补充。
- 品牌基础资料模板：参考 vstorm-co/content-skills 的 BRAND、VOICE、VISUAL 三类文件。
- 国内门店抖音运营：douyin-local-ops 仅作框架参考，其详细内容制作 SOP 尚未建成；部分小项目缺少许可证，复用前需核对。

这些是待试用候选，不是已经采用的依赖、产品架构或首版能力清单。具体选型需随首版任务和成品验收标准收敛，再使用真实品牌资料验证。仓库星数、维护状态、许可证及平台规则均可能变化，采用前应重新核验。

本次只归档调研并补充文档索引；未安装或运行候选 Skill，未连接品牌账号、发送或发布内容，未提交或推送 Git。无关的本机网络信息与内部研究过程不纳入项目资料。
