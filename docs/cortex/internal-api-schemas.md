# Internal / 租户 API 请求与响应（节选）

> 源码：`novaic_cortex/api.py`（**Pydantic `BaseModel`**）。**所有** `/v1/scope/*`、`/v1/context/*`（除 token）、`/v1/meta/*`、`/v1/steps/*`、`/v1/internal/*` 的 body 均含租户字段：**`user_id`**、**`agent_id`**（**`_TenantMixin`**）。

JWT 路由（`/v1/shell` 等）**不**在本文；见 [http-api.md](http-api.md)。

---

## 1. 公共租户块

```json
{ "user_id": "<string>", "agent_id": "<string>" }
```

下文「+」表示在公共块上追加字段。

---

## 2. Scope

| 方法 | 路径 | 请求体（在租户上追加） | 响应（摘要） |
|------|------|------------------------|--------------|
| POST | `/v1/scope/create` | `scope_id`, `name`, `skill?`, `parent_path?`；可选 `phase`, `prev_scope_id`, `wake_triggers`, `handoff_notes`（若 **`api.py`** 中模型含这些字段） | `scope_path` |
| POST | `/v1/scope/end` | `scope_id`, `report?`, `scope_path?`, `is_root` | `ok`, `scope_id`, `archive_path` |
| POST | `/v1/scope/write_assistant` | `scope_id`, `message` (dict), `round_num?` | `ok`, `seq`, `scope_path`（解析后的 active 路径） |

---

## 3. Context（旧式对话缓冲 + 引擎）

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/context/read` | + `scope_id` | `messages` |
| POST | `/v1/context/append` | + `scope_id`, `message` (dict) | `ok` |
| POST | `/v1/context/batch` | + `scope_id`, `messages` (list) | `ok` |
| POST | `/v1/context/prepare_for_llm` | + `scope_id` | `messages`, `stack`, `estimated_tokens` |
| POST | `/v1/context/skill_begin` | + `scope_id`, `skill_name`, `task?` | `ok`, `scope_id`, `child_path`, … 或 `error` |
| POST | `/v1/context/skill_end` | + `scope_id`, `report`, `skill_name?`（Runtime 会带，服务端按 **active** 子 scope 结束） | `ok`, `child_path`, … 或 `warning`/`error` |
| POST | `/v1/context/status` | + `scope_id` | `stack_depth`, `current_skill`, `frames`, `total_messages`, `estimated_tokens`, `usage_ratio` |

---

## 4. Meta

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/meta/read` | + `scope_id` | `meta` |
| POST | `/v1/meta/update` | + `scope_id`, `updates` (dict) | `meta` |

---

## 5. Steps

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/steps/write` | + `scope_id`, `step` (dict) | `path`, `scope_path`（解析后的 active 路径） |
| POST | `/v1/steps/list` | + `scope_id` | `steps`（文件名列表） |
| POST | `/v1/steps/read` | + `scope_id`, `filename` | `step`（dict 或 null） |
| POST | `/v1/steps/index` | + `scope_id` | `entries`（`_index.jsonl` 解析后的列表） |
| POST | `/v1/steps/read_formatted` | + `scope_id`, `tool_call_id`, `provider?`, `include_display?` | `content` |
| POST | `/v1/steps/read_preview` | + `scope_id`, `tool_call_id`, `max_text_len?` | `preview` |

---

## 6. Internal — 工具 / Recall / 重建索引

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/internal/tools` | + `user_id`, `agent_id` | `tools`（builtin 列表） |
| POST | `/v1/internal/recall` | + `token_budget?`（默认 50000） | `content` |
| POST | `/v1/internal/recall_messages` | 同上 | `messages`, `count` |
| POST | `/v1/internal/reindex` | + `force?` | `ok`, `total`, `updated` |

---

## 7. Internal — Shell / Skill（与 JWT 版类似，但无 Bearer）

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/internal/shell` | + `command`, `timeout?` | `stdout`, `stderr`, `exit_code`, `files_changed` |
| POST | `/v1/internal/skill/begin` | + `scope_id`, `name`, `parent_scope_id?` | `Cortex.skill_begin` 返回值 |
| POST | `/v1/internal/skill/end` | + `scope_id`, `instance_id`, `report?` | `Cortex.skill_end` 返回值 |

---

## 8. Token（无租户 mixin）

**`POST /v1/token`**：`user_id`, `agent_id`, `scope_id`, `permissions?`, `ttl?` → **`token`**。

---

## 9. 类型与源码锚点

完整字段以 **`api.py`** 中类定义为准：**`ScopeCreateRequest`**、**`StepWriteRequest`**、**`StepFormattedRequest`** 等。若与本文表格不一致，**以代码为准**。

---

## 相关

- [http-api.md](http-api.md) — 全路由列表  
- [step-index-and-payload-schema.md](step-index-and-payload-schema.md)  
- [session-meta-json.md](session-meta-json.md)  
