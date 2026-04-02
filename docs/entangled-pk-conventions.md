# Entangled 主键（PK）字段约定

> 阶段 0 文档：与 [entangled-architecture-upgrade-plan.md](./entangled-architecture-upgrade-plan.md) 阶段 0.4 对应。

## 单一事实来源

- **Gateway**：`novaic-gateway/gateway/entity/defs.py` 中每个 `EntityDef` 的 `id_field` 与 `primary` 字段定义。

## 客户端（Rust）

- **同步帧**：优先使用服务端下发的 `idField`；缺失时用 `Entangled/packages/client-rust/src/id_field.rs` 的 `default_id_field_for_entity(entity)`（须与 defs 对齐，CI 由单元测试守护）。
- **快照 / prepend**：`cache.rs` 的 `item_id_string` 支持字符串或数字主键（如 `execution-logs` 的整型 `id`）。
- **乐观合并**：`get_list_with_pending` 用同一套 `default_id_field_for_entity(entity)` 匹配行，不得写死 `"id"`。

## 服务端（Python）

- **create 通知**：`entangled/server/store.py` 使用 `_primary_key_value_from_row(result, defn)`，读取 `getattr(defn, "id_field", "id")`。
- **stream head_n / hasMore**：`sync.py` 的 `resolve_sync(..., id_field=...)` 与 `_pk_value_from_row`；`ws_handler` 在 subscribe / load_more 传入 `getattr(defn, "id_field", "id")`。

## 修改实体主键时

1. 改 `defs.py` 的 `id_field` 与字段定义。  
2. 若实体名不变且主键字段名变化：更新 `id_field.rs` 的 match 并跑 `cargo test`。  
3. 检查 Python/Rust 是否仍有 `.get("id")` 假设（`grep`）。  
