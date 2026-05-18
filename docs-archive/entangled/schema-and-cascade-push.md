# Schema 推送与通知机制

> 路径参考：`Entangled/packages/server-python/entangled/server/notifier.py`、`ws_handler.py`

## 核心原则：一次写入 = 一次通知

Entangled 采用最简通知模型：当某个 `(entity, params)` 被写入时，仅向订阅了该精确 `(entity, params)` 的客户端推送 delta。不存在任何自动级联机制。

Gateway 按需写入所需实体，客户端渲染层自行决定是否需要联动更新其他 UI 组件。

## Schema 下发

客户端建立 WebSocket 连接后，服务端立刻下发完整的实体 schema（所有已注册的 `EntityDef` 经 `to_schema_dict()` 序列化）。Schema 包含：

- `keyParams` — 实体的参数化维度
- `syncType` / `syncLimit` — 同步策略（list vs stream）
- `subscriptionMode` — eager（全局实体，连接时自动 entangle）vs lazy（按需）
- `capabilities` — 可用操作（listStream、existsBefore、upsert、actions）

## 订阅（Entangle）流程

1. 客户端发送 `{type: "entangle", entity, params?, version?, depth?}`
2. 服务端直接对该 `(entity, params)` 执行 entangle + resolve_sync
3. 返回 sync 帧（snapshot / delta / head_n）

每个 entangle 请求对应一个实体，无展开、无级联。
