# 内置工具 Schema 与技能安装

> 源码：`novaic-common/common/tools/llm_builtin.py`（LLM-facing builtin schema 权威来源）、`novaic_cortex/api.py`（`/v1/internal/tools` 转发 common schema）、`runtime.py`（技能安装相关 legacy config 读取）。

## 1. 内置 Schema：Common Canonical Tool Schemas

- 静态列表来自 `novaic-common/common/tools/llm_builtin.py`。
- Cortex `/v1/internal/tools` 只作为服务端转发入口，不再拥有另一套 schema authority。
- 用途：作为 **LLM 可调工具** 的唯一服务端合同；Runtime executor、产品语义、Activity Timeline 投影必须与 common schema 对齐。

### 1.1 `skill_begin` 参数（required：`scope_id`, `name`）

| 参数 | 类型 | 说明 |
|------|------|------|
| **`scope_id`** | string | **LLM 自选的全局唯一 id**（示例 `debug-login-1`、`refactor-auth-pass2`）；跨 active + archived 校验，重复拒绝。 |
| `name` | string | 技能名（如 `web-dev`、`debugging`、`code-review`）。 |
| `task` | string? | 该 scope 的简短任务描述，落在 `meta.name`。 |

工具层参数名是 `scope_id`；透到 Cortex HTTP 时重命名为 **`child_scope_id`**（见 [internal-api-schemas.md §3](internal-api-schemas.md#3-context旧式对话缓冲--引擎)），因为 Cortex 侧 `scope_id` 指**会话根**。

### 1.2 `skill_end` 参数（required：`scope_id`, `report`）

| 参数 | 类型 | 说明 |
|------|------|------|
| **`scope_id`** | string | 必须等于当前栈顶 scope_id（LLM 在 **`[Active skill stack]`** 瞬态 system 消息中看到）。 |
| `report` | string | scope 摘要，进入归档 `summary.md`；在下一轮上下文会被折叠为  `"[Skill '{name}' completed]\n{report}"`。 |

严格 LIFO：仅能关栈顶，不匹配报错（不做级联关闭）。详见 [scope-lifecycle.md §9](scope-lifecycle.md#9-skill-scope-生命周期llm-可见栈式)。

当前唯一 summary 写入通路是：LLM 关闭当前栈顶 scope 时调用 `skill_end(report=...)`，`report` 原样成为该 scope 的 `summary.md`。Cortex 不从 `im_reply`、wake 结束、用户画像或其他运行时信号推断 summary。

**并发安全**：`POST /v1/context/skill_begin` 与 `POST /v1/context/skill_end` 在 Cortex API 层以 `(user_id, agent_id, root_scope_id)` 为 key 使用 asyncio 互斥锁（`_SKILL_LOCKS`）串行化，避免同一个 round 里并发 tool_calls 把 stack 状态搞乱。锁条目会在 root scope 归档（`/v1/scope/end` with `is_root=true`）后自动回收。

**结果可见性**：`skill_begin` / `skill_end` 的成功/错误响应均包含 `stack`（LIFO ordered 帧数组，栈顶最先）与 `stack_depth`，工具结果会被 Agent Runtime 当作普通 step 保存到 `steps/`，LLM 在下一轮 prepare_llm_context 可以直接读到。

### 1.3 Runtime finalize

没有 LLM 可调用的 rest/finalize 工具。收尾由 Runtime 在 `react_actions` / `react_think` 里根据 Cortex 栈状态触发：

1. `round_num ≥ runtime.max_rounds_before_force_rest`（默认 40）→ 强制 finalize（保护性兜底，防止 LLM 不 `skill_end` 的死循环）；
2. Cortex 查栈异常（`stack_known=False`）→ fail-safe 继续 think，不 finalize；
3. `stack_depth == 0` ⇒ 开 `wake_finalize` saga；
4. 否则 ⇒ 继续 `react_think` 下一轮。

LLM 要「结束当前工作」只需按 Active scope stack 关闭当前栈顶 scope。`wake_finalize` 只负责生命周期归档、状态切换、MCP 销毁和 session ended 通知；它传给 `/v1/scope/end` 的 `report` 必须为空。

## 2. `initialize()` 种子：`_seed_builtin_tools`

首次 **`Cortex.initialize()`** 时，若对象存储中尚不存在，则写入：

- **`/ro/config/tools/{name}.json`** — 每个 builtin 一条；
- **`/ro/config/tools/_index.json`** — 内置工具名列表。

存储键仍为 **`agents/{agent_id}/ro/config/tools/...`**（见 [object-keys.md](object-keys.md)）。

## 3. `load_tool_schemas()` 合并顺序

1. 扫描 **`/ro/config/tools/*.json`**（排除 `_` 前缀），按目录顺序加载，**同名只保留第一次**（`seen_names`）。
2. 扫描 **`/ro/skills/{skill}/tools/*.json`**，同样按名去重追加。

**先 config 目录，后各 skill**，后者同名不会覆盖前者（已实现为先见者胜）。

## 4. `install_skill(name, skill_md, meta)`

- 校验技能名路径深度 ≤ **`EngineConfig.max_skill_depth`**。
- 写入：
  - **`agents/{agent_id}/ro/skills/{name}/SKILL.md`**
  - **`.../meta.json`**
- **`_rebuild_skill_index()`**：遍历 `.../ro/skills/` 下对象，生成 **`.../ro/skills/_index.md`**（Markdown 列表，含各 `meta.json` 的 `description`）。
- 触发 **`hooks.on_skill_loaded`**（见 extension-points）。
- 更新 **`metrics.skills_installed`**。

返回逻辑路径：**`/ro/skills/{name}/`**。

---

## 相关

- [runtime-facade.md](runtime-facade.md)  
- [engine-config-and-metrics.md](engine-config-and-metrics.md) — `max_skill_depth`  
- [http-api.md](http-api.md) — `GET /v1/tools`、`/v1/skill/list`  
