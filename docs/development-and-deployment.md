# StoreSpark 开发与部署

当前版本是单用户工作台。Web 和未来的小程序共用 `/api/v1` 业务接口，模型 API 密钥只留在后端。当前生成和导出的内容为文本与 Markdown；图片素材用于理解任务，尚不生成海报图片或视频文件。

## Windows 本地开发

需要 Python 3.14 与 Node.js 22.12 及以上。代码声明支持 Python 3.12 及以上，当前 Windows 实测版本为 3.14.6；其他版本需另跑回归。

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
```

首次配置时，将 `.env.example` 复制为 `.env`，已有 `.env` 时保留原文件。使用编辑器填写模型密钥，或服务启动后在工作台的模型设置中填写。不要把真实密钥写入 `.env.example`、前端源码或 Git。

```powershell
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
.\.venv\Scripts\python.exe -m storespark
```

另开终端进入 `web`，首次安装使用 `npm.cmd ci`，启动开发服务：

```powershell
npm.cmd ci
npm.cmd run dev
```

打开 `http://127.0.0.1:5173`。Vite 将 `/api` 转发至后端 `127.0.0.1:8000`，保留原始 Host；不要开启 `changeOrigin`，否则浏览器修改请求会触发同源保护。

也可以在 `web` 执行 `npm.cmd run build`，然后重新启动后端，直接访问 `http://127.0.0.1:8000`。后端会托管 `web/dist`；只运行一个 Python 服务即可使用构建后的页面。

## 模型配置

默认官方 DeepSeek Flash：基础地址 `https://api.deepseek.com`，模型 ID `deepseek-flash`。通过 Chat Completions 调用 JSON Output，实际型号与账户权限以 [DeepSeek 官方文档](https://api-docs.deepseek.com/api/create-chat-completion/)和账户状态为准。

配置优先顺序为工作台保存的配置、服务端环境变量、本地 `.env` 和默认值。尚无保存配置时，系统环境变量优先于 `.env`。支持以下环境字段：

| 变量 | 用途 |
|---|---|
| `LLM_DEFAULT_PROVIDER` | 默认 `deepseek`，也支持 `openai-compatible`。 |
| `DEEPSEEK_BASE_URL` | 模型基础地址，必须使用 HTTPS。 |
| `DEEPSEEK_MODEL` | 发送给供应商的准确模型 ID。 |
| `DEEPSEEK_API_KEY` | 只在服务端读取的模型密钥。 |
| `LLM_TIMEOUT_SECONDS` | 单次模型请求超时，默认 60 秒。 |
| `STORESPARK_DATA_DIR` | 数据目录，默认项目根目录的 `data`。 |
| `STORESPARK_HOST`、`STORESPARK_PORT` | 默认 `127.0.0.1:8000`。 |
| `STORESPARK_ACCESS_TOKEN` | 外部访问必填，至少 24 字符；浏览器通过 Bearer 头发送。 |

工作台保存的模型密钥使用 Fernet 加密写入数据库，主密钥在同一数据目录的 `provider.key` 中。接口只返回是否已配置，不返回密钥或其掩码。留空密钥会保留原值；切换供应商、地址或模型时需要重新填写密钥，避免旧凭据被发送到新接口。保存过的配置优先，修改 `.env` 不会覆盖它。

缺少密钥或模型请求失败时，系统明确返回错误并保留本次输入，不生成伪造成功结果。界面保存配置成功也不代表模型已经联通。

## Linux 部署入口

仓库提供多阶段 `Dockerfile`：Node 构建 Web，Python 镜像以非 root 用户运行 API 和静态页面。运行时只启动一个工作进程，SQLite 和 provider 配置均使用同一个持久数据目录。

在 Linux 服务器准备 Docker Engine 和 Compose，将项目复制到服务器，在根目录创建 `.env`。至少设置一个自行生成的长访问令牌 `STORESPARK_ACCESS_TOKEN`，模型密钥可在 `.env` 或登录工作台后设置。

```bash
docker compose build
docker compose up -d
docker compose ps
```

Compose 只将端口绑定到服务器的 `127.0.0.1:8000`。远程试用可使用 SSH 端口转发；对外提供服务时，需要在前面配置 HTTPS 反向代理。浏览器在模型设置中填写访问令牌后连接。不要把共享访问令牌当作多用户账号系统。

当前实现中的任务锁和配置锁仅在单进程内生效。先保持单实例单进程；增加 worker 或副本前，需要替换任务锁、处理跨进程配置事务并验证存储一致性。

## 数据迁移与备份

任务、对话、素材原始字节及内容都保存在 `storespark.sqlite3`，模型配置主密钥为 `provider.key`。真实素材会在用户发起模型操作时随任务发送给所配置的模型服务。

迁移前先停止旧服务，复制整个数据目录，包括可能存在的 SQLite WAL/SHM 文件和 `provider.key`，再在新环境将 `STORESPARK_DATA_DIR` 指向复制后的目录。停止服务后整体复制可以避免数据库和日志不一致；不要在运行时仅复制主数据库。

Linux 上将数据目录归运行服务的用户所有，并限制其他用户访问。Compose 使用持久卷，容器用户 UID 为 `10001`；迁入持久卷或改用绑定目录时，需要保留文件并调整属主与权限。不要删除旧数据，先在副本上验证任务、素材及加密配置可读，再安排实际切换。

丢失或替换 `provider.key` 会使已保存的模型密钥不可解密，系统不会自动重建并掩盖此问题。应从匹配的备份恢复；不能把密钥加密等同于数据目录泄露后的完整保护。

## 验证命令

后端在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

前端在 `web` 执行：

```powershell
npm.cmd run build
npm.cmd test
```

实际运行记录与尚未验证的项目见 [handoff.md](../handoff.md)。隔离模型测试和页面联调不能代替真实模型、商家反馈或 Linux 部署验证。
