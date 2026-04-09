# 会话 `meta.json`

> 源码：`novaic_cortex/workspace.py`（**`read_session_meta`**、**`update_session_meta`**、**`create_scope`**、**`activate_scope`**、**`complete_child_scope`** / 归档路径）；**`ContextEngine.prepare_messages_for_llm`** 开头读取。

每个 **scope 目录** 下一份：**`{scope_path}/meta.json`**（逻辑路径），经 **`Workspace._sys_write_json`** 写入。

---

## 1. 创建时默认字段（`create_scope`）

| 字段 | 说明 |
|------|------|
| **`name`** | 展示名 |
| **`skill`** | 技能名（可空） |
| **`start_time`** | 浮点时间戳 |
| **`phase`** | **`executing`**（默认）或 **`dormant`**（休眠代理） |
| **`prev_scope_id`** | 可选，链上前一 scope |
| **`wake_triggers`** | 可选，唤醒条件列表 |
| **`handoff_notes`** | 可选，交接说明 |

子 scope 创建时，父级 **`steps/_index.jsonl`** 会追加 **`type: scope`** 行（见 [step-index-and-payload-schema.md](step-index-and-payload-schema.md)）。

---

## 2. 生命周期中可能变化的字段

| 字段 | 典型场景 |
|------|----------|
| **`phase`** | **`executing`** ↔ **`dormant`**；子 scope 结束时 **`archived`**（见 `complete_child_scope` / 归档逻辑） |
| **`activated_at`** | **`activate_scope`** 将 dormant → executing 时写入 |

---

## 3. 与 LLM 拼装的关系（`ContextEngine`）

在 **`prepare_messages_for_llm`** 中，**`meta`** 用于：

| 字段 | 用途 |
|------|------|
| **`system_prompt`** | 若有，作为首条 **`role: system`** |
| **`recall_messages`** | 每项非空 **`content`** → **`role: system`**，**`_metadata.origin: recall`** |
| **`initial_context`** | 多条 **`role`/`content`**，按条追加（冷启动上下文） |

以上字段可由 **`POST /v1/meta/update`** 合并写入（见 [internal-api-schemas.md](internal-api-schemas.md)）。

---

## 4. HTTP

- **`POST /v1/meta/read`**：`{"user_id","agent_id","scope_id"}` → **`{"meta": {...}}`**  
- **`POST /v1/meta/update`**：body 含 **`updates`** dict，与已有 meta **merge**。

---

## 相关

- [scope-lifecycle.md](scope-lifecycle.md)  
- [recall.md](recall.md)  
- [runtime-facade.md](runtime-facade.md)  
