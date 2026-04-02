# Entangled 压测与排障步骤（阶段 2.5）

> 可复现的手工步骤；数值为**基线建议**，非 SLA 合同。

## 桌面（Tauri / `app_bridge`）

1. **环境**

   ```bash
   cd novaic-app/src-tauri
   RUST_LOG=app_bridge=info,app_bridge=warn,entangled_cache=warn cargo tauri dev
   ```

2. **观察字段**

   - `conn_seq`：单次 WebSocket 会话对齐（握手 → 断开）。
   - `slow entangled process_sync`：`process_ms` ≥ 400 时打印，`entity` / `mode`。
   - `entangled sync queue full` / `sync queue still saturated`：有界队列 256 背压。

3. **建议场景**

   - 登录后打开多 Agent / 多会话，观察短时间大量 `sync` 时是否出现队列饱和日志。
   - 断网重连：确认 `resubscribe_all` 后列表恢复，无「恒空」。

## Gateway（Python）

- **事件循环**：`app_client` 已对 `load_more` / `request` 等使用 `create_task`，避免阻塞 `receive_json`。
- **阶段 2.2（已实现）**
  - **`_subscribe_one`**：`subscribe` 后对 `SyncState` 做 **`snapshot_for_resolve`**（同步复制 `op_log`），再 **`await asyncio.to_thread(resolve_sync, …)`**。NovAIC `common.db.Database` 使用 **线程本地 SQLite 连接**，`store.list` / `exists_before` 可在线程中执行。
  - **校正**：线程返回后更新帧内 **`version`**；若 `mode == delta`，用 **`fresh.get_ops_since(client_version)`** 重写 `ops`；若得到 `None`（gap），在主线程再跑一次完整 `resolve_sync`（罕见）。
  - **`handle_load_more`**：`list_stream` + `exists_before` 包在 **`asyncio.to_thread`** 内。
  - **`handle_request` → `_dispatch`**：`list` / `list_stream` / `list_all` / `get` / `create` / `update` / `upsert` / `delete` 在 **`_dispatch_entity_ops_blocking`** 中执行，并由 **`await asyncio.to_thread(...)`** 调用；**`op == "action"`** 仍走 **`await store.action`**（可能异步）。

## 对比记录（模板）

| 日期 | 场景 | 客户端/Gateway 版本 | 现象（P95/日志） |
|------|------|---------------------|------------------|
| 2026-04-01 | CI / 单测（非压测） | 当前分支 | `to_thread` + 推送队列策略已合入；**P95/P99 数值待内网跑表后填入** |
| | | | |
