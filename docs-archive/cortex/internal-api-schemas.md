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
| POST | `/v1/scope/create` | `scope_id`, `name`, `skill?`, `parent_path?`；可选 `phase`, `prev_scope_id`, `wake_triggers`（`handoff_notes` 废弃于 PR-55, 2026-04-23；若 `api.py` 仍接受则被忽略） | `scope_path` |
| POST | `/v1/scope/end` | `scope_id`, `scope_path?`, `is_root`；非空 `report` 会被拒绝 | `ok`, `scope_id`, `archive_path` |
| POST | `/v1/scope/write_assistant` | `scope_id`, `message` (dict), `round_num?` | `ok`, `seq`, `scope_path`（解析后的 active 路径） |
| POST | `/v1/scope/append_input` | `scope_id`, `content`, `role?`, `source?`, `at?`, `message_id?`, `from_kind?`, `from_label?`, `scope_path?` | `ok`, `seq`, `scope_path` |

---

## 3. Context（旧式对话缓冲 + 引擎）

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/context/read` | + `scope_id` | `messages` |
| POST | `/v1/context/append` | + `scope_id`, `message` (dict) | `ok` |
| POST | `/v1/context/batch` | + `scope_id`, `messages` (list) | `ok` |
| POST | `/v1/context/prepare_for_llm` | + `scope_id` | `messages`, `stack`, `estimated_tokens` |
| POST | `/v1/context/skill_begin` | + `scope_id`（根）, **`child_scope_id`**（LLM 选，全局唯一）, `skill_name`, `task?` | `ok`, `scope_id`, `child_path`, `parent_path`, `skill_name` 或 `{ok:false, error}` |
| POST | `/v1/context/skill_end` | + `scope_id`（根）, **`child_scope_id`**（必须 == 当前栈顶）, `report`, `skill_name?` | `ok`, `scope_id`, `child_path`, `summary` 或 `{ok:false, error, stack_top?}` |
| POST | `/v1/context/status` | + `scope_id` | `stack_depth`, `current_skill`, `frames`, `total_messages`, `estimated_tokens`, `usage_ratio` |

---

## 4. Meta

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/meta/read` | + `scope_id` | `meta` |
| POST | `/v1/meta/update` | + `scope_id`, `updates` (dict) | `meta` |
| POST | `/v1/meta/advance_round` | + `scope_id` | `meta`, `round_num`（P2-1：服务端原子 +1） |
| POST | `/v1/meta/counter_inc` | + `scope_id`, `name`, `delta?`（默认 1） | `value`, `name`, `counters`（用于动作级独立限频，例如用户可见 reply action 的 cap） |

---

## 5. Steps

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/steps/write` | + `scope_id`, `step` (dict) | `path`, `scope_path`（解析后的 active 路径） |
| POST | `/v1/steps/list` | + `scope_id` | `steps`（文件名列表） |
| POST | `/v1/steps/read` | + `scope_id`, `filename` | `step`（dict 或 null） |
| POST | `/v1/steps/index` | + `scope_id` | `entries`（`_index.jsonl` 解析后的列表） |
| POST | `/v1/steps/read_formatted` | + `scope_id`, `tool_call_id`, `provider?`, `projection?` (`history` / `current_tool_result` / `display_perception`) | `content` |
| POST | `/v1/steps/read_preview` | + `scope_id`, `tool_call_id`, `max_text_len?` | `preview` |

---

## 6. Internal — 工具 / 重建索引

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/internal/tools` | + `user_id`, `agent_id` | `tools`（builtin 列表） |
| POST | `/v1/internal/reindex` | + `force?` | `ok`, `total`, `updated` |

---

## 7. Internal — Shell（与 JWT 版类似，但无 Bearer）

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/v1/internal/shell` | + `command`, `timeout?` | `stdout`, `stderr`, `exit_code`, `files_changed` |

> P2-2：**`/v1/internal/skill/begin|end` 已删除**。所有 skill 栈变更必须走 `/v1/context/skill_begin` 与 `/v1/context/skill_end`（加锁版本）。

---

## 8. Token（无租户 mixin）

**`POST /v1/token`**：`user_id`, `agent_id`, `scope_id`, `permissions?`, `ttl?` → **`token`**。

---

## 9. Business Internal (Agent 所有权)

| 方法 | 路径 | 鉴权 | 响应 | 失败 |
|------|------|------|------|------|
| GET | `/internal/agents/{agent_id}/owner` | `X-Internal-Key` | `{"agent_id": "...", "user_id": "..."}` | 404 `agent not found` 或 `agent has no owner` |

> 提供权威的 Agent 归属查询（PR-07）。为 `AgentOwnershipResolver` 等下游屏蔽底层 `user_id` 与 `owner_user_id` 的命名差异。

---

## 10. 类型与源码锚点

完整字段以 **`api.py`** 中类定义为准：**`ScopeCreateRequest`**、**`StepWriteRequest`**、**`StepFormattedRequest`**、**`ContextSkillBeginRequest`**、**`ContextSkillEndRequest`** 等。若与本文表格不一致，**以代码为准**。

### 10.1 Skill lifecycle 关键语义（`ContextSkillBeginRequest` / `ContextSkillEndRequest`）

- `scope_id` 是**当前会话根 scope id**（不变，调用方总是传同一个）。
- `child_scope_id` 是**要开/要关的子 scope id**：
  - `skill_begin`：LLM 自选；Cortex 读取 operational SQLite `scope_projection`，发现该 root 下重复 `scope_id` 即拒绝。
  - `skill_end`：Cortex 读取 SQLite active stack projection 的栈顶帧，与 `child_scope_id` 严格比较，不等则拒绝并回传 `stack_top` 给 LLM。
- 详细策略见 [scope-lifecycle.md §9](scope-lifecycle.md#9-skill-scope-生命周期llm-可见栈式)。

---

## 相关

- [http-api.md](http-api.md) — 全路由列表  
- [step-index-and-payload-schema.md](step-index-and-payload-schema.md)  
- [session-meta-json.md](session-meta-json.md)  
