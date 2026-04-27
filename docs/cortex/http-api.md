# HTTP API 分层

> 源码：`novaic_cortex/api.py`（**唯一** `FastAPI` `app`）。**以文件内 `@app.get/post` 为准**；下表与 `api.py` 顶部三层注释一致。

## 1. 三层路由

| 层 | 认证 | 典型调用方 |
|----|------|------------|
| **Agent Tool API** | **`Authorization: Bearer`** + `auth.verify_capability_token` | Sandbox 内工具（shell、skill） |
| **CLI API** | 同上 | `novaic` CLI（read/write/ls/recall/tools/proxy） |
| **Internal API** | **无** Bearer；body 里带 **`user_id` / `agent_id`**（`_TenantMixin`） | Agent Runtime worker |

另有 **`GET /health`**（无业务认证）、**`POST /v1/token`**（签发能力 JWT，**不要求**已有 Bearer）。

---

## 2. 路由清单（与实现一致）

### Agent Tool API（JWT）

| 方法 | 路径 |
|------|------|
| POST | `/v1/shell` |
| POST | `/v1/skill/begin` |
| POST | `/v1/skill/end` |

### CLI API（JWT）

| 方法 | 路径 |
|------|------|
| GET | `/v1/read` |
| POST | `/v1/write` |
| GET | `/v1/ls` |
| GET | `/v1/skill/list` |
| GET | `/v1/recall` |
| GET | `/v1/tools` |
| POST | `/v1/proxy/{command}` |

### Internal — Scope

| 方法 | 路径 |
|------|------|
| POST | `/v1/scope/create` |
| POST | `/v1/scope/end` |
| POST | `/v1/scope/write_assistant` |
| POST | `/v1/scope/list_summaries` |

> `/v1/scope/list_summaries` (PR-57)：批量读最近 K 个**已归档根 scope** 的 `summary.md`。请求 `{user_id, agent_id, limit?, exclude_scope_ids?}`；响应 `{summaries: [{scope_id, summary, archived_at, depth}, ...]}`，按 `archived_at` 从老到新。Runtime `handle_session_init` 用它构造 `<PREV_SCOPE_HISTORY>` 注入块（见 [scope-lifecycle.md §10](scope-lifecycle.md#10-跨-root-rolling-summary-history)）。

### Internal — Context

| 方法 | 路径 |
|------|------|
| POST | `/v1/context/read` |
| POST | `/v1/context/append` |
| POST | `/v1/context/batch` |
| POST | `/v1/context/prepare_for_llm` |
| POST | `/v1/context/skill_begin` |
| POST | `/v1/context/skill_end` |
| POST | `/v1/context/status` |

### Internal — Meta / Steps

| 方法 | 路径 |
|------|------|
| POST | `/v1/meta/read` |
| POST | `/v1/meta/update` |
| POST | `/v1/meta/advance_round` |
| POST | `/v1/meta/counter_inc` |
| POST | `/v1/steps/write` |
| POST | `/v1/steps/list` |
| POST | `/v1/steps/read` |
| POST | `/v1/steps/index` |
| POST | `/v1/steps/read_formatted` |
| POST | `/v1/steps/read_preview` |

### Internal — 其它

| 方法 | 路径 |
|------|------|
| POST | `/v1/internal/tools` |
| POST | `/v1/internal/recall` |
| POST | `/v1/internal/recall_messages` |
| POST | `/v1/internal/reindex` |
| POST | `/v1/internal/shell` |

> `/v1/internal/skill/begin|end` 已删除（P2-2）。Skill 栈变更走 `/v1/context/skill_begin` 与 `/v1/context/skill_end`。

### 签发与健康

| 方法 | 路径 |
|------|------|
| POST | `/v1/token` |
| GET | `/health` |

---

## 3. 与 Runtime 的衔接

Agent Runtime 通过 **`POST /v1/context/prepare_for_llm`** 取 **messages + tools**，与 [context-timeline-and-dfs.md](context-timeline-and-dfs.md) 中的 **`ContextEngine`** 一致。  
请求/响应字段见 [internal-api-schemas.md](internal-api-schemas.md)。

---

## 相关

- [internal-api-schemas.md](internal-api-schemas.md) — Internal 路由 body 摘要  
- [proxy-cli-auth.md](proxy-cli-auth.md) — JWT vs Business `X-Internal-Key`  
- [proxy-gateway-routes.md](proxy-gateway-routes.md) — `/v1/proxy/{command}` → Business  
- [runtime-facade.md](runtime-facade.md) — `Cortex` 类  
