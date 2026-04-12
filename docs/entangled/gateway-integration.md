# 网关端 Entangled 集成（Gateway Integration）

> **2026-04**：与 `novaic-gateway/gateway/entity/store.py`、`scripts/start.sh` 一致。旧文描述的 **`GatewayEntityStore(db, defs, runtime, vmuse_mgr)`** 构造与「仅嵌入一层」叙述已过时，仅作历史参考。

## 1. 当前实现：`EntityStore` 与 `RemoteEntityStore`

- **`EntityStore`**（`gateway/entity/store.py`）：继承 `entangled.sql.SqlEntityStore`，CRUD 走本地 SQLite（`gateway.db`）。
- **`RemoteEntityStore`**：当 `ServiceConfig` 中 **`ENTANGLED_URL` / `ENTANGLED_SERVICE_URL` 非空** 时，`get_entity_store()` 返回该类。

### Entity Routing Split

`LOCAL_ONLY_ENTITIES = {users, refresh-tokens, api-keys, vm-users, models, api-key-models}` 留 `gateway.db`，其余（`devices` 等需同步到客户端的实体）代理到 Entangled HTTP。

- **`_local_store`** 注册**所有** entity 定义（含 remote 的），但只对 LOCAL entities 建表（`ensure_schema`）。这保证 `_scope_where` 的 parent 链查找正常（如 `vm-users.parent = ("devices", ...)`）。
- 写操作经 **`EntangledServiceClient`** 调用独立 Entangled HTTP，并带 **`X-Notify: false`**；同步帧由 Gateway 侧 **`_notify_change` → `/app/ws`** 投递。
- **Pre-delete hook**（`_cleanup_device_on_pc_client`）：`devices` entity 删除前向 PC Client 发 `vm_delete`（先 shutdown 再 `DELETE /api/vms/{id}` 删磁盘）/ `android_avd_delete` / `host_desktop_stop`，确保 WS entity delete 与 HTTP REST `DELETE /api/devices/{id}` 行为一致。
- **`device_actions.py` → `_get_device_and_repo`**：先尝试 `DeviceRepository`（gateway.db），找不到时回退到 `EntityStore`（Entangled），用 `device_from_dict` 构造 Device 对象。`get_status_action` 自行处理状态查询，不再依赖只读 gateway.db 的 HTTP 端点。

可选覆盖：`NOVAIC_ENTANGLED_URL` 在 ServiceConfig 层覆盖 JSON 中的基址（见 `common/entangled_url.py`）。

## 2. 内部 API 与 Worker 路径

- **`/internal/entities/*`**（`gateway/api/internal/entity.py`）：无鉴权，供内网调用；在 Remote 模式下与 `RemoteEntityStore` 一致：**Entangled HTTP `notify=false` + `remote_notify_after_entangled_http_write`**。
- **`POST /internal/entangled/sync-notify`**：Runtime/Worker 在 **直连 Entangled HTTP** 且 `notify=false` 成功后，将 **`entity` / `action` / `data` / `params`** 交给 Gateway，由同一套 notifier 推送到 **`/app/ws`**。`novaic-agent-runtime` 的 **`GatewayBusinessClient`** 在 Remote 模式下对 `entity_*` 写操作自动调用该接口。

## 3. 历史：从双层胶水到 `entangled.sql`

早期 Gateway 曾用大量手写 SQL 与中层胶水对接 Entangled；现已收敛为 **`entangled.sql` 单栈** + 上述 Remote/Local 分支。业务钩子（序列化 `serializer`/`deserializer`、迁移热修等）仍在 `EntityStore` 子类中，见 `store.py`。

## 相关

- 独立 Entangled 对照清单：`docs/roadmap/entangled_standalone_checklist.md`
- App WS 与稳定性：`docs/architecture/entangled-store-and-app-ws.md`
- 客户端 WS 策略（契约）：`docs/entangled/client-ws-strategy.md`
