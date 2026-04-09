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
| 单个后端（仍会触发**全量**远端重启） | `./deploy runtime` / `./deploy cortex` / `./deploy storage-a` 等 |
| Relay（QUIC） | `./deploy relay` |
| LLM Factory | `./deploy factory` |
| iOS IPA | `./deploy ios` |
| macOS 桌面包 | `./deploy desktop` |
| 一键：前端 + 全后端 + relay + iOS + 桌面 | `./deploy all [version]` |
| 状态 | `./deploy status` |
| 日志 | `./deploy logs [gateway\|cortex\|tools\|runtime\|worker\|relay]` |
| 重置某用户登录密码（api 机 `gateway.db`） | `./deploy reset-password <email>`（可选环境变量 `NOVAIC_DEPLOY_NEW_PASSWORD`） |

## 行为说明

- **`deploy gateway`**：同步 `novaic-common`、`novaic-gateway`、`Entangled`，再 SSH 执行 `bash /opt/novaic/start.sh --stop && bash /opt/novaic/start.sh`。
- **`deploy services`**：对上述及 `novaic-agent-runtime`、`novaic-storage-a`、`novaic-cortex` 等批量 rsync，再统一 `start.sh` 重启。
- 远端服务目录默认为 **`/opt/novaic/services/<name>/`**。

## 相关

- 总览与排障：**[`HANDOVER.md`](../../HANDOVER.md)**（根目录）。
- 架构与端口：**[`../architecture/overview.md`](../architecture/overview.md)**。
