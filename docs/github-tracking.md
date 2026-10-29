# StoreSpark GitHub 任务跟踪

更新日期：2026-10-28。仓库为 [Eclipseic1848/StroeSpark](https://github.com/Eclipseic1848/StroeSpark)，沿用用户创建的仓库拼写，产品工作名为 StoreSpark。

用户已授权同步推送工程，并在 GitHub 创建和执行相关 Issues。远端初始 `main` 提交 `7d437661ea47e5ddf712d728f301b32c1e04e5bb` 只含 README，作为本轮提交的父历史保留，不强制覆盖。

| Issue | 内容 | 当前执行状态 |
|---|---|---|
| [#1](https://github.com/Eclipseic1848/StroeSpark/issues/1) | 上传请求体在解析前限额 | 已关闭。9 项新增回归通过，代码已推送；Windows/Linux 后端 CI 通过。 |
| [#2](https://github.com/Eclipseic1848/StroeSpark/issues/2) | Web 工作台与完整交互 | 已关闭。构建、5 项 Chromium 检查及实际 API 浏览器联调通过，包含保存裁剪和开发代理同源回归；远端 Linux 构建与交互检查通过。 |
| [#3](https://github.com/Eclipseic1848/StroeSpark/issues/3) | 跨平台安装、部署和持续检查 | 已关闭。依赖锁、部署和迁移文档已交付；Windows/Linux 后端、Web、非 root Linux 容器启动与重启持久化 CI 均通过。 |
| [#4](https://github.com/Eclipseic1848/StroeSpark/issues/4) | 真实 DeepSeek 和商家任务验证 | 未完成；需要用户本机模型凭据及真实商家资料和反馈，不以隔离响应替代。 |
| [#5](https://github.com/Eclipseic1848/StroeSpark/issues/5) | 模型地址和异常授权头输入边界 | 已关闭。4 项新增检查和原 42 项通过，已推送并在 Windows/Linux CI 通过。 |

实现提交为 [84e4e0c](https://github.com/Eclipseic1848/StroeSpark/commit/84e4e0cf60dcbec4084d7e027737ead420d7a0f6)，[CI Run 40800541934](https://github.com/Eclipseic1848/StroeSpark/actions/runs/40800541934) 的四项作业均成功，Issue 已写入相应验收记录。后续文档提交不改变该实现提交的工程证据。

GitHub CI 绿色仅代表相应工程检查通过，不代表真实模型联通、商家采用或经营效果成立。#4 保持开放，真实密钥应在用户本机模型设置或服务端 `.env` 配置，不上传至 Issue 或聊天。
