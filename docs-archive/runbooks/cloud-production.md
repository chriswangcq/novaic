# 云端生产与部署

> 与当前脚本/拓扑一致；对应原 `**HANDOVER.md` §六、§七**。**主机、端口、SSH** 以仓库根 `**./deploy`** 内变量与线上实际为准（下列为 HANDOVER 记载的参考值）。

## 统一部署 CLI（`./deploy`）

```bash
# ── 客户端 ──
./deploy frontend [ver]    # 构建前端 + rsync 到 relay OTA（默认版本见 deploy 内 VERSION）
./deploy ios               # 构建 IPA + 安装到已连接 iPhone
./deploy desktop           # 构建 macOS .app

# ── 后端服务 (api.gradievo.com) ──
./deploy gateway           # rsync + start.sh 全部重启
./deploy runtime           # novaic-agent-runtime
./deploy blob-service      # Blob Service（实现目录：novaic-blob-service）
./deploy cortex            # novaic-cortex（:19996）
./deploy services          # rsync 全部 + start.sh 重启（推荐）
# 注意：无 ./deploy orchestrator（RO 子模块已删除）

# ── 基础设施 ──
./deploy relay             # rsync + cargo build + systemctl（见 deploy 实现）
./deploy factory           # rsync + systemctl restart llm-factory

# ── 运维 ──
./deploy status / logs [svc] / all [ver]
```

**原理**：`./deploy` **只负责 rsync 同步代码**，进程管理交给服务器端 `**/opt/novaic/start.sh`**。

> 旧的单独 Gateway 重启脚本已删除。单独重启 Gateway 易导致状态不一致。**所有重启应走 `start.sh`。**

更细的子命令说明见 `**[deploy.md](deploy.md)`**。

## Gateway（api.gradievo.com）


| 项目   | 值                                                                                  |
| ---- | ---------------------------------------------------------------------------------- |
| SSH  | `ssh root@api.gradievo.com`                                                        |
| 代码路径 | `/opt/novaic/services/novaic-gateway`                                              |
| 数据目录 | `/opt/novaic/data/`                                                                |
| 数据库  | `/opt/novaic/data/gateway.db` (SQLite)                                             |
| 配置   | `/opt/novaic/services/novaic-common/config/services.json`；可选运行时覆盖 `/opt/novaic/etc/runtime_switches.json` |
| 日志   | `tail -f /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log`；App WS：`grep -E 'AppWS |


**Gateway 启动参数（示例）**：

```
--host 127.0.0.1 --port 19999 --data-dir /opt/novaic/data
--queue-service-url http://127.0.0.1:19997
--blob-service-url http://127.0.0.1:19995
```

**Nginx**（`/etc/nginx/sites-enabled/novaic`）：

- `auth_request → /internal/auth/validate`，注入 `X-User-ID`，剥离客户端伪造头
- CloudBridge WebSocket `/internal/pc/ws` 超时 3600s
- 前端 OTA `/api/config/frontend` 无需 JWT，限流 burst=30

**后端 Python 进程（HANDOVER 记载）**：5 HTTP 服务 + 4 task-worker + 2 saga-worker + health + scheduler + STUN 等共 **14** 个进程表述（随 `start.sh` 演进以线上为准）。

## Relay / STUN（relay.gradievo.com）


| 项目      | 值                                                |
| ------- | ------------------------------------------------ |
| SSH     | `ssh -p 52222 root@47.243.221.45`（以 deploy 为准）   |
| 代码路径    | `/opt/novaic/novaic-quic-service`                |
| systemd | `novaic-quic-service.service`                    |
| 端口      | STUN 3478 UDP / Relay 443 QUIC / Nginx 80/443 静态 |


**部署**：`./deploy relay`（或手动 pull + `cargo build` + `systemctl restart`）

**前端热更新**：

```bash
./deploy frontend 0.3.0
```

客户端通过 Gateway `/api/config/frontend` 获取 OTA URL；Gateway 的生产值来自 `services.json`，不再读取退役 env file。

**OTA 三处同步**（新增 CDN 域名须同时改）：


| 位置                                                       | 修改项                 |
| -------------------------------------------------------- | ------------------- |
| `novaic-app/src/config/index.ts`                         | `OTA_ORIGINS`       |
| `novaic-app/src-tauri/capabilities/remote-frontend.json` | `remote.urls`       |
| `novaic-app/src-tauri/src/setup.rs`                      | `OTA_ALLOWED_HOSTS` |


CI：`scripts/check-ota-sync.sh`。

## LLM Factory（newapi.gradievo.com）


| 项目      | 值                                                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| SSH     | `ssh root@newapi.gradievo.com`                                                                                                       |
| 代码路径    | `/opt/novaic/llm-factory`                                                                                                            |
| 端口      | 19990（`llm-factory.service`）                                                                                                         |
| 部署      | `./deploy factory`                                                                                                                   |
| 运维日志 UI | `https://api.gradievo.com/factory-logs`（密钥见 Nginx `/factory-api/` 的 `$factory_key`；页面 `novaic-llm-factory/static/factory-logs.html`） |


**API 端点**：


| 端点                                          | 用途             |
| ------------------------------------------- | -------------- |
| `POST /v1/chat/completions`                 | **唯一 LLM 出口**  |
| `GET/POST/DELETE /v1/config/api-keys/`*     | 管理 API Key     |
| `GET/POST/PUT/DELETE /v1/config/models/*`   | 管理模型           |
| `POST /v1/config/api-keys/{id}/test`        | 测试 Key         |
| `GET /v1/config/api-keys/{id}/fetch-models` | 拉取 provider 模型 |
| `GET /v1/logs`                              | 调用日志           |


已删除：`/resolve`（曾返回明文 api_key）、`/defaults`（迁至 Gateway）。

## 服务器数据维护


| 项目          | 命令                                                                                                                                |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Queue 已完成任务 | `sqlite3 queue.db "DELETE FROM tq_tasks WHERE status IN ('done','failed'); DELETE FROM tq_sagas WHERE status!='active'; VACUUM;"` |
| 日志轮转        | `find /opt/novaic/data/logs/ -name '*.log' -mtime +7 -delete`                                                                     |
| 日志截断        | `find /opt/novaic/data/logs/ -name '*.log' -size +50M -exec truncate -s 10M {} \;`                                                |


> **禁止**运行时执行 `PRAGMA wal_checkpoint(TRUNCATE)`（截断未提交事务）。

**Gateway 卡死恢复（示例）**：

```bash
kill -9 $(pgrep -f main_gateway.py) && sleep 2
rm -f /opt/novaic/data/gateway.db-wal /opt/novaic/data/gateway.db-shm
bash /opt/novaic/start.sh
```
