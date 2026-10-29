# StoreSpark 开发暂停记录

记录性质：此前用户要求暂停时的历史快照。用户已于 2026-10-28 明确要求继续，并授权 GitHub 同步与 Issues 执行。当前状态以 [handoff.md](../handoff.md)和[GitHub 任务跟踪](github-tracking.md)为准，以下保留原暂停现场。

## 本次已确认的方向

- 用户已同意产品流程，并授权开始代码编写。
- 开发环境为 Windows，最终考虑迁移到 Linux 服务器，也可能上架微信小程序。
- 用户要求借鉴 Mangrove 的模型 provider 配置方式，并提供 DeepSeek Flash，已明确为官方直连。
- 当前默认基础地址为 `https://api.deepseek.com`，模型 ID 为 `deepseek-flash`，以 [DeepSeek 官方接口文档](https://api-docs.deepseek.com/api/create-chat-completion/)及 Mangrove 当前连接目录为依据。
- 当前实施选择为 Python FastAPI + SQLite 后端、React + TypeScript + Vite Web 客户端。API 与 Web 分离，未来小程序可另做客户端；尚无小程序代码。

## 已写入的代码与配置

| 位置 | 当前内容 |
|---|---|
| `storespark/settings.py`、`__main__.py` | 服务端环境配置及跨平台启动入口，默认监听本机；监听外部网络前要求访问令牌。 |
| `storespark/store.py` | SQLite 任务、对话、素材、内容和 provider 设置保存。 |
| `storespark/schema.py`、`workflow.py`、`app.py` | 请求校验、模型提示、任务与素材 API、宣传方向、文本生成与修改、人工编辑、Markdown 导出。 |
| `storespark/provider.py` | DeepSeek 及兼容接口调用；单个生效配置，保存配置优先于环境配置；密钥加密保存、不回显；空白密钥保留原值，切换配置时要求重新填写。 |
| `tests/test_provider.py`、`tests/test_workflow.py` | provider 与业务 API 隔离测试，不调用真实模型。 |
| `pyproject.toml`、`.env.example`、`.gitignore` | Python 依赖、服务端配置示例及密钥/数据/构建产物忽略规则。 |
| `web/` | 已写部分前端基础与组件，尚不能启动，详见下节。 |

仅只读参考 Mangrove 源码，未修改其仓库，未读取其 `.env`、数据库或真实密钥，未迁移其数据。

## 前端中断位置

已写入 `web/package.json`、`index.html`、`tsconfig.json`、`vite.config.ts`、`src/types.ts`、`src/api.ts`、`src/main.tsx`，以及 `src/components/` 下的 `Shared.tsx`、`CreateTask.tsx`、`Settings.tsx`、`ContentEditor.tsx`。

`App.tsx`、`styles.css`、`TaskWorkspace.tsx` 和根目录 `DESIGN.md` 尚未创建。`npm install` 已中断，退出码为 1；`web/node_modules` 存在，`web/package-lock.json` 不存在。不能把这个目录视作已安装完成，也不能声称前端构建或浏览器验证通过。

工作台空态概念图已生成并查看，保留在本机：

`C:/Users/55672/.codex/generated_images/01a17c22-94a0-7621-8c9d-d42acef2a375/exec-7b0416f1-d883-43fc-a09c-3669dbba90b6.png`

概念图尚未复制进仓库，也不代表可运行页面或已验收设计。不要删除已有前端文件或安装残留来掩盖未知状态；恢复时先检查。

## 已完成的验证

后端在本项目 `.venv` 安装成功，使用 Python 3.14.6。当前安装快照包括 FastAPI 0.162.0、Uvicorn 0.54.0、HTTPX 0.28.1、cryptography 49.0.0 和 Pillow 12.3.0；项目声明 Python 3.12 及以上，其他版本未实测。

以下命令实际通过，共 31 项测试，其中 provider 20 项、业务流程 11 项：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试覆盖四种任务起点、素材基本校验、模型失败保留输入、不产生虚假成功、内容编辑和导出、重新打开数据库后读取、密钥加密与不回显、配置变更校验及访问令牌。使用 HTTPX 隔离模型传输，不代表真实 DeepSeek 调用成功。重启验证为重新创建应用读取同一数据目录，尚未启动并重启实际服务进程。

测试出现 Starlette 对 HTTPX TestClient 的弃用警告；测试通过，兼容升级尚未处理。

## 已确认但尚未修复的问题

**上传请求的体积限制发生得太晚。** `storespark/app.py` 的文件读取上限在 FastAPI 完整解析 multipart 后执行。只读复现通过 ASGITransport 上传 16 MB TXT，最终返回 413、没有素材入库，但 Starlette 已向临时文件写入 16,777,216 字节。超大请求仍可能先占用临时磁盘。

恢复时应优先在 multipart 解析前限制上传请求体，并对没有 `Content-Length` 的流式请求累计限额；补充可复现回归检查后再继续发布相关工作。用户要求暂停后未实施该修复。

## 未完成与未验证

- 未启动实际 API 开发服务器，未做 Web/API 浏览器联调、前端构建或真实模型请求；未创建 `.env`。
- 暂停检查时项目 `data` 目录不存在；测试数据使用临时目录，未产生真实商家数据。
- 未形成 Python 依赖锁文件，前端依赖安装尚未完成。
- `Dockerfile`、`docker-compose.yml` 均未创建。Docker CLI 存在，但 Linux Engine 管道不可连接，当前不能做容器实测。
- 未验证 Linux 运行、真实服务重启、同任务并发及生产运行。现有任务锁和 provider 配置锁只支持单进程。
- 当前内容交付为文本与 Markdown，无海报图片渲染、视频成片或联网调研。商家需求、内容质量及经营效果均未现实验证。
- 尚无微信登录、支付、小程序客户端、多用户隔离或生产发布。自动发布等产品边界仍未最终定案。

## Git 与恢复入口

本地仍为 `main`，没有提交；原有文档与新增代码均未跟踪，未暂存、提交或推送。`.venv`、安装残留、密钥、数据和前端构建目录由 `.gitignore` 忽略。保留全部工作现场。

用户要求继续后，先读 [handoff.md](../handoff.md) 并核对 Git 和文件现状。优先处理已复现的上传限制问题；随后补齐前端及安装、构建和联调，再完善依赖锁定与 Linux 部署入口，最后在用户本机安全配置模型密钥后验证真实调用。不要将本次暂停自动解释为开发完成或发布授权。
