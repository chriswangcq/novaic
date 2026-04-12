# Entangled 独立进程 — 实现对照清单

> 用途：按条对照代码与运维行为，**慢工出细活**逐项收口。  
> 状态：`[x]` 已对照仓库实现满足；`[ ]` 未做或仅部分满足；`[~]` 有已知限制需后续跟进。  
> 最后核对：仓库快照（以 `main_gateway.py`、`store.py`、`scripts/start.sh` 等为准）。

---

## 图例

| 符号 | 含义 |
|------|------|
| `[x]` | 行为在代码中可追溯，与设计一致 |
| `[~]` | 可用，但有文档/协议/运维层面的已知差异或技术债 |
| `[ ]` | 未实现、未在本仓库、或需单独排期 |

---

## A. 进程启动与端口

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| A1 | Entangled 在 Gateway 之前启动 | 读 `scripts/start.sh` 顺序 | `[x]` | 先 `entangled.app.main`，`wait_port` 后再起 Gateway（约 L75–94） |
| A2 | 默认端口 19900 | grep `PORT_ENTANGLED` / `services.json` | `[x]` | `start.sh` L19–25；`novaic-gateway/config/services.json` / `novaic-agent-runtime/config/services.json` |
| A3 | Gateway 传入 `--entangled-url` | `start.sh` 与 `main_gateway.py` argparse | `[x]` | `start.sh` L92；`main_gateway.py` `--entangled-url`，并写入 `ServiceConfig.ENTANGLED_URL` / `ENTANGLED_SERVICE_URL` |
| A4 | JWT / 服务 token 注入 Entangled 与 Gateway | 环境变量 | `[x]` | `start.sh` `JWT_SECRET`、`ENTANGLED_SERVICE_TOKEN`；schema push 用 `ENTANGLED_SERVICE_TOKEN` 或 `JWT_SECRET`（`main_gateway.py` lifespan） |
| A5 | `stop` 同时结束 Entangled 与 Gateway | `pkill` 模式 | `[x]` | `start.sh` `stop`：`entangled.app.main` 与 `main_gateway.py`（L53–56） |

---

## B. 配置与单点真相

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| B1 | `ServiceConfig` 含 `ENTANGLED_URL` / `ENTANGLED_SERVICE_URL` | `common/config.py`（gateway 包） | `[x]` | 与 `services.json` 中 `entangled_service.url` 一致 |
| B2 | CLI `--entangled-url` 覆盖配置文件中的 URL | `main_gateway.py` 启动段 | `[x]` | 写入 `ENTANGLED_URL` 与 `ENTANGLED_SERVICE_URL` |
| B3 | Worker 与 Gateway 使用同一 Entangled 基址 | 运行时读 `ServiceConfig` | `[x]` | **`NOVAIC_ENTANGLED_URL`** 在 `common/entangled_url.py` 中覆盖 `services.json`；`scripts/start.sh` 导出与 `ENTANGLED_URL` 一致。Gateway 仍可用 `--entangled-url` 覆盖（见 `main_gateway.py`） |
| B4 | 环境变量覆盖 Entangled HTTP URL（不经 JSON） | `NOVAIC_ENTANGLED_URL` | `[x]` | 见 `novaic-common/common/entangled_url.py`；`strict_config` 仍只读 JSON，覆盖在 **ServiceConfig 层** 生效 |

---

## C. Gateway：实体层与 DDL

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| C1 | 注册全部实体定义 | `register_all_entities()` | `[x]` | `main_gateway.py` lifespan |
| C2 | 有 `ENTANGLED_URL` 时向 Entangled `POST /v1/schema/register` | `schema_push.push_schemas_to_entangled` | `[x]` | `main_gateway.py`；`gateway/entity/schema_push.py` |
| C3 | 有 `ENTANGLED_URL` 时 **跳过** 本地 `ensure_all_schemas` | lifespan 分支 | `[x]` | `main_gateway.py`：有 URL则 push；无则 `ensure_all_schemas()` |
| C4 | `get_entity_store()` 在 URL 非空时为 `RemoteEntityStore` | `store.py` | `[x]` | `_remote_entangled_enabled()` + `RemoteEntityStore()` |
| C5 | `RemoteEntityStore` 将 CRUD/高级操作代理到 HTTP | `store.py` 中类 | `[x]` | `list`/`_sql_*`/`batch_update`/`append`/`update_where` 等 |
| C6 | 远端写操作抑制 Entangled 进程内 notify、由 Gateway `_notify_change` 推 App WS | `EntangledServiceClient` `notify=False` + `EntityStore` 包装 | `[x]` | `RemoteEntityStore` + `internal/entities` + `GatewayBusinessClient` 写路径一致 |
| C7 | `init_entangled()` / SyncRegistry / `set_entangled_store` | `gateway/entity/entangled_bridge.py` | `[x]` | 仍存在；`app_client` 连接时 `_init_entangled_once()` |

---

## D. Entangled 独立服务（本仓库 Python 包）

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| D1 | HTTP CRUD + schema + count/batch 等 | `entangled/app/crud.py` | `[x]` | 与 `EntangledServiceClient` 对齐；含 `notify` 头、`/list`、`/exists-before`、`/update-where` 等 |
| D2 | WebSocket `/v1/sync` 调用 `ws_handler` 正确签名 | `entangled/app/ws.py` | `[x]` | `handle_subscribe(sender, store, user_id, client_id, data)` 等 |
| D3 | Notifier `push_fn(event, payload)` 同步调度发送 | `ws.py` `sync_push` | `[x]` | 与 `create_ws_handler` 一致：入队 **`PUSH_QUEUE_MAX_SIZE`**，consumer `send_json`；背压 drop-oldest |
| D4 | 独立 WS 首帧 schema 与 Gateway `/app/ws` **完全一致** | 对比 JSON 形状 | `[x]` | `/v1/sync` 与 `ws_handler.create_ws_handler` 一致：`type: "push"`、`event: "schema"`、`data.entities` + `hash` + `syncContractVersion`（无 `entangledWsUrl`，因已直连） |
| D5 | 独立 WS 具备与 `create_ws_handler` 相同的 heartbeat/背压 | 对比 `ws_handler` | `[x]` | `ws.py`：`PUSH_QUEUE_MAX_SIZE` 队列 + drop-oldest、`HEARTBEAT_INTERVAL_S` / `HEARTBEAT_TIMEOUT_S`、入站刷新 `last_activity` |

---

## E. 运行时 Worker（`novaic-agent-runtime`）

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| E1 | `GatewayBusinessClient` 实体 CRUD 走 `EntangledServiceClient` | `task_queue/client.py` | `[x]` | `entity_get/update/list/create/append` + Remote 下 **`sync-notify`** |
| E2 | 关闭 client 时释放 Entangled HTTP 会话 | `client.py` `close` | `[x]` | 需随代码确认 `entangled.close()` |
| E3 | 文档/注释与「走 Entangled」一致 | 读类注释 | `[x]` | `GatewayBusinessClient` 类注释已写明 Entangled HTTP + `/internal/entangled/sync-notify` |

---

## F. 推送与多端一致性（架构债）

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| F1 | Worker 直写 Entangled 后，桌面/App **仍能**收到与 Gateway 相同的 sync 帧 | 端到端 | `[x]` | **`GatewayBusinessClient`**：`notify=False` + **`POST /internal/entangled/sync-notify`**；其它直连 Entangled 的调用方须自行中继或改用 `/internal/entities/*` |
| F2 | `POST /internal/entities/*` 与 `RemoteEntityStore` notify 策略一致 | 读 `internal/entity.py` | `[x]` | Remote 模式下 **`notify=False` + `remote_notify_after_entangled_http_write`**；与 `RemoteEntityStore` 对齐 |
| F3 | `GET /api/entangled/schema` 与 WS schema 含 `entangledWsUrl`（可选直连） | `entangled.py`、`app_client.py` | `[x]` | `gateway/infra/entangled_ws.py`；有独立 URL 时返回 |

---

## G. 前端与仓库外

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| G1 | 桌面/Web 客户端消费 `entangledWsUrl` 或仅用 `/app/ws` | 契约文档 | `[x]` | **`docs/entangled/client-ws-strategy.md`**（实现仍在 **`novaic-app`**） |
| G2 | Nginx 反代 `/v1/sync`、TLS、超时 | 示例配置 | `[x]` | **`nginx-entangled-ws.example.conf`**：`proxy_buffering off`、长超时、生产 checklist 注释 |

---

## H. 文档一致性

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| H1 | `docs/entangled/gateway-integration.md` 与当前 `EntityStore`/`RemoteEntityStore` 一致 | 人工 diff | `[x]` | 已重写为 Remote/Local、internal、Worker 中继 |
| H2 | 架构文写清「独立 Entangled + Gateway 双进程」 | `docs/architecture/*` | `[x]` | `overview.md`、`entangled-store-and-app-ws.md` 已补充 |

---

## I. 测试与 CI

| ID | 项 | 验证方式 | 状态 | 证据 / 备注 |
|----|----|----------|------|----------------|
| I1 | Sync Contract / schema 单测 | `tests/unit/gateway/test_sync_contract_schema.py` | `[x]` | CI `tauri-ci.yml` 引用 |
| I2 | `RemoteEntityStore` + mock HTTP 集成测试 | 搜索 `RemoteEntityStore` in tests | `[x]` | `tests/unit/gateway/test_remote_notify.py`（`remote_notify_after_entangled_http_write` + mock） |
| I3 | CI 冒烟（进程或包级） | workflows | `[x]` | **`tauri-ci.yml`**：`Entangled server-python import smoke`（`entangled.app.ws/crud`）；全进程 **`python -m entangled.app.main`** 留部署/集成环境 |

---

## J. 建议执行顺序（一个接一个）

1. ~~**运维**：固定 B3 / B4 — `NOVAIC_ENTANGLED_URL` + `start.sh` 导出~~（已做）  
2. ~~**协议**：D4 — `/v1/sync` schema 首帧已与 `/app/ws` 对齐~~（已做）  
3. ~~**产品/协议**：F1 — Worker：`notify=False` + `/internal/entangled/sync-notify`；`GatewayBusinessClient` 自动中继~~（已做）  
4. ~~**代码**：F2 — `internal/entity.py` 与 `RemoteEntityStore` 对齐~~（已做）  
5. ~~**文档**：H1、H2~~（已做）  
6. ~~**测试**：I2 + CI 步骤~~（已做）；全进程 I3 冒烟仍可选  
7. ~~**D5**：`/v1/sync` heartbeat/背压~~（已做）  
8. ~~**G1/G2/I3**：客户端契约文档、Nginx 示例、CI Entangled import smoke~~（已做）

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-04-11 | 初版：对照 `scripts/start.sh`、`main_gateway.py`、`store.py`、`entangled/app/ws.py`、`internal/entity.py`、配置与清单讨论结论 |
| 2026-04-11 | F1/F2/D5、internal 路由、`sync-notify`、`test_remote_notify`、文档与 CI |
| 2026-04-11 | `client-ws-strategy.md`、`entity_append`、Nginx 示例、`sync-notify` action 校验、CI Entangled import smoke |
