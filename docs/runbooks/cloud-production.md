# 云端生产与部署原理

> 对应 **`HANDOVER.md` §六、§七**。IP/主机名以脚本 **`./deploy`** 与当前运维为准。

## `./deploy` 原理

- **本地 rsync** 到远端 **`/opt/novaic/services/<name>/`**（或 relay/factory 对应路径）。
- **进程**由远端 **`/opt/novaic/start.sh`** 统一管理；**不要**只重启单个 Gateway 而不走 `start.sh`（否则易不一致）。
- 常用命令摘要见 [**`deploy.md`**](deploy.md)。

## Gateway（api）

| 项 | 典型值 |
|----|--------|
| 代码 | `/opt/novaic/services/novaic-gateway` |
| 数据 | `/opt/novaic/data/`、`gateway.db` |
| 日志 | `/opt/novaic/data/logs/gateway-YYYYMMDD.log` |
| 监听 | `127.0.0.1:19999`（Nginx 对外 443） |

- Nginx：`auth_request` → `/internal/auth/validate`；CloudBridge WS 长超时；详见 HANDOVER §7.1。
- **进程数**：多台 Python 服务 + workers（具体数以线上 `start.sh` 为准）。

## Relay / STUN

- `novaic-quic-service`：STUN、`novaic-quic-service` systemd、静态资源等。
- **OTA 静态资源**：`rsync` 到 relay 机 `static/vX/`；Gateway **FRONTEND_CDN_URL** 需指向新前缀。

## LLM Factory（newapi）

- 典型端口 **19990**；`POST /v1/chat/completions` 为统一 LLM 出口。
- 运维日志 UI：`https://api.gradievo.com/factory-logs`（密钥与 Nginx 配置一致；页面源码在子模块 `novaic-llm-factory`）。

## 数据维护（慎用）

| 操作 | 说明 |
|------|------|
| Queue 清理 | SQLite 删除已完成 task/saga 等（见 HANDOVER 命令） |
| 日志 | 轮转、截断大文件 |
| Gateway 卡死 | 可 kill 后删 `-wal/-shm` 再 `start.sh`（见 HANDOVER） |

**禁止**：运行时 **`PRAGMA wal_checkpoint(TRUNCATE)`**（会截断未提交事务）。
