# `steps/_index.jsonl` 与 Payload Manifest

> 源码：`novaic_cortex/workspace.py`（**`write_step`**、**`write_assistant`**、**`write_env`**、**`write_inline_env`**、**`read_step_index`**）；渲染：**`context_stack/engine.py`**。

统一时间线索引文件：**`{scope_path}/steps/_index.jsonl`**，一行一个 JSON 对象，顺序即时间线。

---

## 1. 索引行类型：`type` 字段

| `type` | 含义 | 通常是否有 `file` |
|--------|------|-------------------|
| **`env`** | 环境/用户侧事件、唤醒、内联标记 | 有（写文件）或 **无**（纯内联） |
| **`assistant`** | 一轮 LLM assistant 输出 | **有**（`ast_*.json`） |
| **`tool`** | 工具调用与结果 | **有**（`NNNN_tool_*.json`） |
| **`scope`** | 子 scope（技能）节点 | **`file`** 为子目录名 + `/` |

---

## 2. `tool` 步（`write_step`）

**磁盘文件**：`{scope_path}/steps/{seq:04d}_{step_type}_{step_id}.json`（`step_type` 默认 **`tool`**）。

**写入时传入的 `step` dict**（节选，以代码为准）：

| 字段 | 说明 |
|------|------|
| **`type`** | 默认 `"tool"` |
| **`call_id`** / **`id`** | 步标识，用于文件名；**不得**含 `/`、`..`、NUL |
| **`tool`** | 可选，记入索引 |
| **`status`**、**`started_at`**、**`duration_ms`**、**`result_id`**、**`artifacts`** | 可选，影响索引行 |

**索引行**（`write_step` 追加）包含：`seq`、`type`、`id`、`status`、`ts`、`file`；可选 `tool`、`duration_ms`、`result_id`、`has_artifacts`、`step_ref`、`payload_ref`。

**渲染为 LLM**（**`_render_tool`**）：读 JSON 文件，**`role: tool`**，**`tool_call_id`** = 文件内 **`call_id`** 或索引 **`id`**，**`content`** = **`result`**（dict 则 `json.dumps`）。

### 2.1 Payload Manifest 语义权威

工具输出的完整 payload 不由 Blob Service 承担语义。当前主路径是：

1. `Workspace.write_step` 规范化 step，并把完整 payload 交给 `Workspace.write_payload`。
2. `Workspace.write_payload` 写 scope-local `payloads/*.json` 记录，并同步写 SQLite `payload_manifest`。
3. 小 payload 的 manifest 使用 `retention_class="scope_local"`，`blob_ref=NULL`。
4. 大 payload 外置到 Blob Service，manifest 使用 `retention_class="external_blob"`，`blob_ref=blob://...`。
5. `payload_manifest` 记录 `payload_ref`、`source_payload_ref`、`root_scope_id`、`scope_id`、`step_ref`、`size_bytes`、`sha256`、`status`、`retention_class`、`error` 等语义字段。

Blob Service 只保存外置 payload 的原始字节；payload 的可用性、错误状态、生命周期和归属语义由 Cortex operational SQLite 的 `payload_manifest` 负责。

读取 payload 时，`Workspace.read_payload` 会先读 scope-local payload record，再按 manifest/record 中的 `blob_ref` 获取外置字节。失败不会再表现为裸 `KeyError` / `ValueError`：Cortex 会抛出结构化 `PayloadReadError`，并把 manifest 更新为 `missing`、`corrupt` 或 `unavailable`。

---

## 3. `assistant` 步（`write_assistant`）

**磁盘文件**：**`ast_{seq:03d}.json`**（注意与 tool 的 **4 位 seq** 命名差异）。

**文件内容**：来自 Runtime 的 **`message`**（`role`/`content`/`tool_calls`/`reasoning_content` 等）+ **`ts`**、**`round`**。

**索引行**：`seq`、`type: assistant`、`round`、`ts`、`file`；若含 tool_calls 则 **`has_tool_calls: true`**。

**渲染**（**`_render_assistant`**）：读出上述字段填入 **`assistant`** 消息。

---

## 4. `env` 步

### 4.1 有文件（`write_env`）

**索引行**含 **`file`** 指向 **`steps/`** 下 JSON；**`_render_env`** 当前主要使用带 **`text`** 的条目（见 engine）；具体 **`subtype`** 与载荷以 **`write_env`** 写入为准。

### 4.2 无文件（`write_inline_env` / 部分 env）

**索引行**可含 **`text`**（及 **`subtype`** 等），**`_render_env`**：有 **`text`** 则生成 **`role: system`**。

**`create_scope`（`phase=="dormant"`）** 会写一条 **`type: env`、`subtype: scope_dormant`** 的索引行（无 `file`）。

---

## 5. `scope` 步（子技能）

父 scope 的 **`_index.jsonl`** 中 **`type: scope`**，**`file`** 为子目录名 + **`/`**（如 **`0003_scope_skill-xxx-abc12345/`**）。

**`ContextEngine._render_scope`**：拼 **`{root}/steps/{file}`** 为子 **`scope_path`**，读子 **`meta.json`**；若 **`phase == archived`** 则折叠为一条 system（**`summary.md`**）；否则递归 **`_render_all_steps`** 并加 **`[Skill '…' active]`** 头。

---

## 6. 与全局 **`/ro/scopes/_index.jsonl`** 的区别

- **`steps/_index.jsonl`**：单个 scope 内**时间线**，供 **`ContextEngine`** 遍历。  
- **`/ro/scopes/_index.jsonl`**：**根 scope 归档索引**，保留作历史兼容/排障索引；当前 LLM 主路径不走独立 Recall。

---

## 相关

- [session-meta-json.md](session-meta-json.md)  
- [context-timeline-and-dfs.md](context-timeline-and-dfs.md)  
- [internal-api-schemas.md](internal-api-schemas.md) — `/v1/steps/*` 请求体  
