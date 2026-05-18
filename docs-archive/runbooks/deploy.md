# 部署（Runbook）

父仓库根目录 **`deploy`** 为统一部署入口：本地 **rsync** 到远端，进程由服务器上的 **`/opt/novaic/start.sh`** 管理（不在本机 `nohup` 长期跑）。

> **原理、Gateway/Relay/Factory 主机表、OTA 三处同步、维护命令** 的完整版见 [**`cloud-production.md`**](cloud-production.md)。本节为命令速查。

细节以仓库内 **`./deploy` 源码**为准。

## 前置

- 已配置对 **`api.gradievo.com`**、**relay**、**Factory 机** 等的 SSH（脚本内写死主机别名，见 `deploy` 顶部变量）。
- 子模块目录存在且可同步（如 `novaic-gateway`、`novaic-app`）。

## 常用命令

| 目标 | 命令 |
|------|------|
| 前端 OTA | `./deploy frontend [version]`（默认版本见脚本内 `VERSION`） |
| 仅 Gateway + Entangled 等网关侧 | `./deploy gateway` |
| 全部后端（多 submodule rsync + 远端 `start.sh`） | `./deploy services` |
| 单个后端（仍会触发**全量**远端重启） | `./deploy runtime` / `./deploy cortex` / `./deploy blob-service` 等 |
| Relay（QUIC） | `./deploy relay` |
| LLM Factory | `./deploy factory` |
| iOS IPA | `./deploy ios` |
| macOS 桌面包 | `./deploy desktop` |
| 一键：前端 + 全后端 + relay + iOS + 桌面 | `./deploy all [version]` |
| 状态 | `./deploy status` |
| 新鲜部署烟测 | `./deploy fresh-smoke [epoch]` |
| 日志 | `./deploy logs [gateway\|cortex\|tools\|runtime\|worker\|relay]` |
| 重置某用户登录密码（api 机 `gateway.db`） | `./deploy reset-password <email>`（可选环境变量 `NOVAIC_DEPLOY_NEW_PASSWORD`） |

## 行为说明

- **`deploy gateway`**：同步 `novaic-common`、`novaic-gateway`、`Entangled`，再 SSH 执行 `bash /opt/novaic/start.sh --stop && bash /opt/novaic/start.sh`。
- **`deploy services`**：对上述及 Runtime、Blob Service、Cortex 等批量 rsync，安装 Blob/Cortex/Runtime 独立 venv 依赖，再统一 `start.sh` 重启。
- 远端服务目录默认为 **`/opt/novaic/services/<name>/`**。
- 后端重启会先在远端记录一个 epoch 秒时间戳，再执行 `start.sh`，最后用 timestamp-aware fresh-smoke 检查关键日志文件的 mtime 是否都在重启前的时间戳之后。这个检查用于避免把旧日志 tail 当成新部署证据。
- 如需人工复核，运行 `./deploy fresh-smoke [epoch]`；省略 `epoch` 时默认检查远端最近 15 分钟内的关键后端日志是否更新。
- `start.sh` 会在启动完成后验证 required runtime subprocesses。role-level roster 的 SSOT 是 `novaic-agent-runtime/task_queue/workers/runtime_roster.py`，远端 shell 通过 `novaic-agent-runtime/scripts/runtime_worker_roster.py` 读取；当前包括 `task-worker control`、`task-worker execution`、`saga-worker`、`session-outbox-worker`、`saga-outbox-worker`、`health`、`scheduler`、`subscriber`。数量不匹配会让启动失败。`subscriber` 日志是 `subscriber.log`。
- `./deploy status` 同样按 role-level worker roster 输出 expected/actual 计数，不再只输出一个粗粒度 worker 总数。

## 相关

- 总览与排障：**[`HANDOVER.md`](../../HANDOVER.md)**（根目录）。
- 架构与端口：**[`../architecture/overview.md`](../architecture/overview.md)**。
