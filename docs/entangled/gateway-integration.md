# 网关端 Entangled 集成（Gateway Integration）

> **⚠️ 2026-04-16 更新**：本文档大部分内容已过时。当前架构中：
> - Gateway 不再拥有 `RemoteEntityStore` 或 `EntangledServiceClient`
> - Gateway 仅保留 `AuthEntityStore`（本地 SQLite，管理 users/refresh-tokens）
> - 所有非 LOCAL_ONLY 的 entity CRUD 通过 `GatewayBusinessEntityClient` → Business `/internal/entities/*` → Entangled
> - Workers 通过 `BusinessClient.entity_*` → Business → Entangled
> - Device Service 通过 `BusinessEntityClient` → Business → Entangled
> - **仅 Business Service 直连 Entangled HTTP**

> **2026-04**：旧文描述的 **`GatewayEntityStore(db, defs, runtime, vmuse_mgr)`** 构造与「仅嵌入一层」叙述已过时，仅作历史参考。

## 1. 当前实现：`AuthEntityStore`（Gateway 本地）+ Business 代理

- **`AuthEntityStore`**（`gateway/entity/store.py`）：本地 SQLite（`gateway.db`），仅管理 `users`、`refresh-tokens` 等认证相关实体。
- **`GatewayBusinessEntityClient`**：Gateway 对所有非本地实体的 CRUD，通过 HTTP 代理到 **Business Service** `/internal/entities/*`，由 Business 直连 Entangled HTTP。

### Entity Routing Split

`AuthEntityStore` 仅处理认证实体（`users`、`refresh-tokens` 等），留在 `gateway.db`。其余所有业务实体（`devices`、`messages` 等）通过 `GatewayBusinessEntityClient` → Business `/internal/entities/*` → Entangled HTTP。

- Gateway **不再**拥有 `RemoteEntityStore` 或 `EntangledServiceClient`。
- 写操作经 **Business Service** 调用 Entangled HTTP，并带 **`X-Notify: false`**；同步帧由 Business 侧通知机制投递。
- **设备生命周期管理**（删除、状态等）由 **Business Service** 的 `DeviceOrchestrator` 负责编排，Gateway 不再直接参与设备操作。

可选覆盖：`NOVAIC_ENTANGLED_URL` 在 ServiceConfig 层覆盖 JSON 中的基址（见 `common/entangled_url.py`），但该配置仅对 Business Service 生效。

## 2. 内部 API 与 Worker 路径

- **Business `/internal/entities/*`**（`business/internal/entity.py`）：无鉴权，供内网调用；Business 直连 Entangled HTTP `notify=false` + 推送通知。
- **Workers**：通过 `BusinessClient.entity_*` → Business `/internal/entities/*` → Entangled HTTP。Workers 不再直连 Entangled。
- **Device Service**：通过 `BusinessEntityClient` → Business `/internal/entities/*` → Entangled HTTP。
- **Gateway**：通过 `GatewayBusinessEntityClient` → Business `/internal/entities/*` → Entangled HTTP。
- **Business Service 是唯一直连 Entangled HTTP 的服务**。

## 3. 历史：从双层胶水到 Business 中枢

早期 Gateway 曾用大量手写 SQL 与中层胶水对接 Entangled，后收敛为 `RemoteEntityStore` + Local 分支。当前架构进一步演进：Gateway 退化为薄边缘网关（Auth, App WS, TURN, File Proxy），所有 Entangled 交互收归 **Business Service（:19998）** 统一管理。

## 相关

- 独立 Entangled 对照清单：`docs/roadmap/entangled_standalone_checklist.md`
- App WS 与稳定性：`docs/architecture/entangled-store-and-app-ws.md`
- 客户端 WS 策略（契约）：`docs/entangled/client-ws-strategy.md`
