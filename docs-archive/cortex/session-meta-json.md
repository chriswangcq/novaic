# 会话 `meta.json`

> 源码：`novaic_cortex/workspace.py`（**`read_session_meta`**、**`update_session_meta`**、**`create_scope`**、**`activate_scope`**、**`complete_child_scope`** / 归档路径）。

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
| ~~`handoff_notes`~~ | **已废弃 (PR-55, 2026-04-23)** — 原拟承载 LLM 自述交接笔记，但驱动工具 `subagent_rest` 从未在 `BUILTIN_TOOL_SCHEMAS`，字段全生命周期为 NULL。meta.json 新建时不再写入；旧 scope 的遗留值可被忽略。 |

子 scope 创建时，父级 **`steps/_index.jsonl`** 会追加 **`type: scope`** 行（见 [step-index-and-payload-schema.md](step-index-and-payload-schema.md)）。

---

## 2. 生命周期中可能变化的字段

| 字段 | 典型场景 |
|------|----------|
| **`phase`** | **`executing`** ↔ **`dormant`**；子 scope 结束时 **`archived`**（见 `complete_child_scope` / 归档逻辑） |
| **`activated_at`** | **`activate_scope`** 将 dormant → executing 时写入 |

---

## 3. 与 LLM 拼装的关系

当前 `ContextEngine.prepare_messages_for_llm` 的主输入是 `context.jsonl` 与 `steps/`，不会从 `meta.json` 读取一条独立 Recall 或 wake-summary 通道。`meta.json` 主要记录 scope 生命周期属性与少量配置性字段。

历史上部分 scope 可能含有这些字段：

| 字段 | 用途 |
|------|------|
| **`system_prompt`** | 历史/兼容字段；当前系统提示由 Runtime prompt builder 注入 |
| **`recall_messages`** | 历史字段；当前主路径不注入独立 Recall |
| **`initial_context`** | 历史/兼容字段；当前上下文以 `context.jsonl` + Step Tree 为准 |

以上字段可由 **`POST /v1/meta/update`** 合并写入（见 [internal-api-schemas.md](internal-api-schemas.md)）。

---

## 4. HTTP

- **`POST /v1/meta/read`**：`{"user_id","agent_id","scope_id"}` → **`{"meta": {...}}`**  
- **`POST /v1/meta/update`**：body 含 **`updates`** dict，与已有 meta **merge**。

---

## 相关

- [scope-lifecycle.md](scope-lifecycle.md)  
- [recall.md](recall.md)（历史/已退役）
- [runtime-facade.md](runtime-facade.md)  
