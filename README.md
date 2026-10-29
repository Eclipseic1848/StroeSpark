# StoreSpark

StoreSpark 是面向餐饮店主、门店运营和品牌运营人员的营销助手项目。当前正在完成首版 Web 工作台，支持任务、素材、宣传方向、文本内容生成与修改、编辑保存和 Markdown 导出。

产品拟通过对话和素材提交理解经营诉求，帮助商家确定宣传方向，生成适配不同场景的营销内容，并提供使用和验证建议。期望的业务结果是吸引消费者进店尝试，实际效果尚待验证。

## 当前状态

- 项目工作名：StoreSpark。
- 中文候选名：店有招，由助手建议，尚未最终确认。
- 候选宣传语：让门店特色，成为进店理由。
- 优先面向餐饮行业，后续考虑向快消行业扩展。
- GitHub 仓库：[Eclipseic1848/StroeSpark](https://github.com/Eclipseic1848/StroeSpark)，项目工作名仍为 StoreSpark。执行状态见[GitHub 任务跟踪](docs/github-tracking.md)。
- 当前采用 Python FastAPI + SQLite 后端、React + TypeScript + Vite Web 客户端，面向 Windows 开发、未来 Linux 部署及可能的小程序客户端。
- 后端 64 项检查通过；Web 构建、5 项浏览器交互及实际 API 联调通过。既有[Windows/Linux、Web 和 Linux 容器 CI](https://github.com/Eclipseic1848/StroeSpark/actions/runs/40800541934)均已通过，最新提交状态以 Actions 为准。
- 官方 DeepSeek Flash 真实调用已验证，并针对素材外宣传属性与重复追问做了[来源约束修复和真实对比](docs/verification/content-grounding-2026-10-28.md)。最终四组样本通过有限检查与人工复核，失败候选保留，不代表普遍消除幻觉或商家验收完成。
- 用户已于 2026-10-28 要求继续，并授权推送工程及在 GitHub 创建和执行 Issues。此前的[暂停记录](docs/development-checkpoint.md)保留为历史现场。

## 本地运行

在项目根目录安装后端依赖并启动，默认仅本机访问：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m storespark
```

首次运行前可用 `python -m venv .venv` 创建虚拟环境。另开终端进入 `web`，执行 `npm.cmd ci` 和 `npm.cmd run dev`，访问 `http://127.0.0.1:5173`。先在模型设置中填写自己的 DeepSeek 密钥，或使用服务端 `.env`。不配置密钥也能保存任务和素材，不能发起模型处理。

完整安装、构建后单服务运行、Linux 容器、访问令牌、数据迁移与备份见[开发与部署](docs/development-and-deployment.md)。

## 文档入口

| 文档 | 用途 |
|---|---|
| [handoff.md](handoff.md) | 新会话首先阅读，了解当前状态和下一步 |
| [产品定义初稿](docs/product-definition.md) | 当前产品概念、明确要求和未定边界 |
| [产品流程草案](docs/product-flow-draft.md) | 需求输入、澄清、宣传方向、内容生成、修改与交付的建议流程，含四种用户起点和待验证边界 |
| [开发暂停记录](docs/development-checkpoint.md) | 已写代码、已通过检查、已确认缺陷、未完成前端及恢复顺序 |
| [开发与部署](docs/development-and-deployment.md) | Windows 启动、模型配置、Linux 容器入口、数据备份与验证命令 |
| [GitHub 任务跟踪](docs/github-tracking.md) | 本轮 Issues、验收边界及实际执行状态 |
| [DeepSeek 真实调用验证](docs/verification/deepseek-live-2026-10-28.md) | 四种起点、真实成功与失败、空标题修复及尚未完成的商家验证 |
| [宣传事实与追问质量修复](docs/verification/content-grounding-2026-10-28.md) | 来源边界、正反例回归、真实对比及各候选版本失败记录 |
| [需求与决策记录](docs/discovery-log.md) | 用户反馈、确认过程、假设和待验证事项 |
| [内容制作 Skill 与模板调研](docs/research/content-skills-landscape-2026-10-26.md) | 品牌、快消、零售与餐饮领域的 13 个候选项目、具体资源、适配分析和局限 |
| [AGENTS.md](AGENTS.md) | 本项目的协作、语言、编码和实施约定 |

补充资料：[内容制作 Skills 和模板调研](docs/research/content-skills-landscape-2026-10-26.md)。该文件在本轮整理期间新增，本轮保留原文，未复核其调研结论，不代表已采用其中的技术方案。

## 已确认的关键要求

使用者可以带着明确任务，也可以只有模糊的经营诉求；可以提交已有素材，也可以从零准备开始。产品应根据现有信息逐步追问，帮助技术小白收敛任务，同时承接已有明确思路和素材的用户。

一次任务的交付包括宣传方向、对应场景的可用成品，以及使用和验证建议。多场景、多格式属于产品方向，首版具体支持清单尚未确定。

## 继续推进

本轮工程已推送并完成验收，Issues #1、#2、#3、#5 已关闭。下一步由 [#4](https://github.com/Eclipseic1848/StroeSpark/issues/4) 跟踪真实模型与商家任务验证。成品质量标准、首版场景与格式范围，以及自动发布、广告投放、数据来源和收费方式仍需继续收敛。

资料更新日期：2026-10-28。详细状态以交接说明及对应需求记录为准。
