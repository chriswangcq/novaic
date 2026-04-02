# Entangled 订阅参数（params）规范化

> 阶段 1.4：减少 Python `json.dumps(sorted items)` 与 Rust `hash_params` 对「同一逻辑订阅」算出不同 key 的风险。

## 服务端（Python）

- `entangled/server/sync.py` 中 `_state_key` 使用 **`Dict[str, str]`** 经 `sorted(params.items())` 再 `json.dumps`。
- **约定**：写入 registry 的 params **仅字符串标量**；数字/布尔在入 registry 前转为十进制字符串（如 `"42"`、`"true"`）。

## 客户端（Rust）

- `CacheKey` 使用 `serde_json::Map<String, Value>` 的 `hash_params`：键排序后对每个 `Value` 使用 **`to_string()`** 再哈希。
- **约定**：Tauri/前端传入的 params 对象应与服务端字符串化结果一致（例如 JSON 数字 `42` 的 `to_string()` 为 `42`，与 Python `"42"` 在字节上仍可能不同 — **推荐 WS 层统一字符串 params**）。

## 检查清单（人工 / 未来 CI）

- [x] Python：`tests/test_params_state_key.py` 固定 `_state_key` 向量（排序、空 params）。
- [ ] Rust：`hash_params` 使用 `std::collections::hash_map::DefaultHasher`，**哈希值随 Rust 版本可能变**；CI 只断言稳定性与排序不变性，不把 u64 当作跨语言 golden。
- [ ] 对 `messages` + `{ "agent_id": "<uuid>" }` 在「仅字符串 params」路径下联调，确认订阅分区与 Gateway `_state_key` 一致。
- [ ] 不在 params 中使用 `null` 与省略键混用表示同一语义。

## 前端（React Query `queryKey`）

- `novaic-app` 使用 `buildEntangledQueryKey` / `buildEntangledQueryKeyFromParams`（`data/entangled/client.ts`）：对参与分区的键做 **字典序排序** 后再取 value 序列，与 Rust `EntityChanged.params` 经 `entities_changed` 送达后的排序方式一致。
- Schema 里的 `keyParams`（camelCase）与 WS 帧里的 params 键（多为 snake_case）在**多键**场景下应保证排序后的 **取值顺序** 与订阅分区一致；单键场景仅一个 value，通常无歧义。

## 主键字段 `idField`（与 params 独立）

- Gateway 生成 `gateway/entity/generated_entity_id_fields.json`；**Rust** `entangled-client` 在 `build.rs` 中据此生成 `default_id_field_for_entity`；**TS** 侧 `defaultIdFieldForEntity` 读 `generated_entity_id_fields.json`。
- 变更 defs 后：`python novaic-gateway/scripts/export_entity_id_fields.py` 并执行仓库根目录 `scripts/sync_entity_id_fields.sh`。

## 与升级计划的关系

阶段 **1.5**：双端以**同一套 params 形状**验收（Python 字符串 key；Rust `Map<String, Value>` 与 `to_string()` 约定），而非比较 `_state_key` 字符串与 `params_hash` 数值。
