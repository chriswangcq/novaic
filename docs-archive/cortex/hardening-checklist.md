# NovAIC Agent Runtime + Cortex — Hardening Checklist

> **历史检查单**：本文基于 2026-04-17 的架构评审，保留用于追溯当时 P0-P3 加固项。当前主路径已迁移到 agent-root / wake scope / `skill_end(report=...)` / `wake_finalize`；遇到 `subagent_rest`、auto meta skill 等术语时，按历史上下文理解，不作为当前实现契约。
>
> 基于 [architecture-review-2026-04-17.md](./architecture-review-2026-04-17.md) 的 8 位架构师评审 + 8 位 summarizer 汇总，整理成**可执行、可勾选、可追溯**的四阶段清单。
>
> 状态标记：`[ ]` 未做、`[x]` 已完成、`[~]` 进行中、`[!]` 已确认为假警报（无需做）。
>
> 每项都携带 ID（方便 PR/commit 引用）、来源架构师、严重度、证据位置、验收标准。

**Release gating rule**: Phase 0 未清零前不允许上线新容量；Phase 1 未清零前不允许 Cortex 多 worker 或水平扩容。

---

## Phase 0 — Correctness blockers（阻塞上线，优先做）


| ID   | Status | Item                                                                            | 来源         |
| ---- | ------ | ------------------------------------------------------------------------------- | ---------- |
| P0-1 | `[!]`  | ~~注册 `react_think` / `subagent_rest` saga~~（假警报）                                | Arch#1, #6 |
| P0-2 | `[x]`  | `write_step` 返 `None` 时 handler 判为失败                                            | Arch#3     |
| P0-3 | `[x]`  | `SessionRepository.dispatch` 检查 `INSERT OR IGNORE` rowcount，loser 返 `deduped`   | Arch#2     |
| P0-4 | `[x]`  | `handle_cortex_skill_end` / `handle_cortex_scope_end` 失败时 raise（对齐 skill_begin） | Arch#3, #5 |
| P0-5 | `[x]`  | `react_think` no-tool 终止前强制 `check_stack`，`stack_depth>0` 不得 rest               | Arch#4     |
| P0-6 | `[x]`  | `_SKILL_LOCKS` 增加 TTL/LRU 淘汰，防弃置会话泄漏                                            | Arch#7     |
| P0-7 | `[x]`  | `get_cortex_bridge` cache key 改为 `(scope_id, user_id, agent_id)`                | Arch#1, #8 |


### P0-1 ~~Saga 未注册~~（假警报）

- 核查结果：`task_queue/sagas/__init__.py` 自动导入 4 个模块全部存在；`saga_worker.py:300-303` 枚举 4 类 saga_type。关闭。

### P0-2 `write_step` 返 None 判为失败

- 证据：`task_queue/handlers/context_handlers.py:115-123`、`task_queue/utils/cortex_bridge.py:291-306`（`write_step` 吞异常返 None）。
- 验收：`result is None` → raise（HTTP 错误由 saga 重试），或返 `success: False`。
- 回归：单测：mock bridge.write_step 返 None，handler 必须抛错。
- 受影响 saga：`react_actions` 的 `save_results` 并发分支。

### P0-3 dispatch INSERT OR IGNORE loser 语义

- 证据：`queue_service/session_repo.py:150-170` 未读 `rowcount`；loser 已 `orchestrator.create(saga_type=subagent_wake)`，产生孤儿 saga。
- 验收：
  - 若 rowcount == 0 → 从 `tq_active_sessions` 读回 winner 的 `saga_id/scope_id`，`mark_failed` 或丢弃 loser saga，返回 `{action: "deduped", saga_id, scope_id}`。
  - 相同 (agent_id, subagent_id) 并发 10 次 → 仅 1 条 active session、1 条 `saga_started`，其余为 `deduped` 且同一个 `saga_id/scope_id`。
- 回归：加 sqlite 并发测试。

### P0-4 skill_end / scope_end raise 对齐 skill_begin

- 证据：`task_queue/handlers/cortex_handlers.py:42-48`（scope_end）、`109-114`（skill_end）当前 `except → return success:True`，与 `skill_begin:73-87` 的 raise 不对称。
- 验收：skill_end 在 `ok: false` 或 HTTP 错误下 `raise RuntimeError`；scope_end 归档失败同样 raise（归档是幂等的：meta.json `active → archived`）。
- 兼容：保留「Cortex disabled」short circuit。

### P0-5 react_think 终止前必须 check_stack

- 证据：`sagas/react_think.py:119-136, 176-186, 228-232` no-tool-after-retry → 直接 `trigger_terminate` → `subagent_rest`，绕过栈检查。
- 验收：在 `trigger_terminate` 前加一步 `CORTEX_CHECK_STACK`，`stack_depth > 0` 时改走 retry_think 或注入 system warning 要求先 `skill_end`。
- 回归：mock LLM 连续返 empty tool_calls，stack 非空 → 不得进入 rest。

### P0-6 `_SKILL_LOCKS` TTL 清理

- 证据：`novaic-cortex/novaic_cortex/api.py` 只在 `is_root` scope_end 成功时 `_drop_scope_lock`。被遗弃的 root scope（agent 异常退出、saga 失败未走 compensation）永不清理。
- 验收：
  - 方案 A：`WeakValueDictionary` + 定期扫 key 对应 root scope meta（`archived` 或超过 TTL）清掉。
  - 方案 B：LRU with size cap（比如 10k），超出时按 LRU 淘汰。
  - 目标：24h soak test 下 `len(_SKILL_LOCKS)` 稳定。

### P0-7 bridge cache 复合 key

- 证据：`task_queue/utils/cortex_bridge.py:518-536` 仅以 `scope_id` 做 key。UUID 碰撞概率虽低但逻辑不安全。
- 验收：key 改为 `(scope_id, user_id, agent_id)`；`remove_cortex_bridge(scope_id)` → `remove_cortex_bridge(scope_id, user_id, agent_id)` 或按 scope_id 扫描清除。

---

## Phase 1 — Near-term integrity（Phase 0 之后 1-2 周）


| ID    | Status | Item                                                                                   | 来源     |
| ----- | ------ | -------------------------------------------------------------------------------------- | ------ |
| P1-1  | `[x]`  | Cortex 步骤写入串行化（per root）防 `_index.jsonl` 丢失更新                                          | Arch#2 |
| P1-2  | `[x]`  | `cortex_bridge` 写路径失败改为 raise，只有只读路径软失败                                                | Arch#3 |
| P1-3  | `[x]`  | `log_cortex` 强制可用（移除 try/except fallback）并补 `skill_begin/end` 事件                       | Arch#6 |
| P1-4  | `[x]`  | `_decide_rest_or_continue` 输出结构化 decision log（含 scope_id/round_num/stack_depth/reason） | Arch#6 |
| P1-5  | `[x]`  | `subagent_rest` 携带 `rest_reason` 与 `round_num`                                         | Arch#4 |
| P1-6  | `[x]`  | `context.read` 幂等：Runtime 侧按 `_idempotency_key` 去重 append                              | Arch#1 |
| P1-7  | `[x]`  | `cortex_bridge` 错误字段统一用 `error`（不用 `warning`）                                          | Arch#5 |
| P1-8  | `[x]`  | Cortex skill_begin HTTP 路径强制 `max_skill_depth`                                         | Arch#4 |
| P1-9  | `[x]`  | 确认 `observability.py` 已随 Cortex 部署（否则日志不落盘）                                            | Arch#6 |
| P1-10 | `[x]`  | `subagent_rest` 自身失败的 watchdog（避免 stuck awake）                                         | Arch#3 |


### P1-1 per-root 步骤写锁

- Evidence: `novaic-cortex/novaic_cortex/workspace.py:427-465` `write_step` = `_count_step_dirs` + `_sys_append_line`（RMW），非并发安全。
- 方案：复用 `_SKILL_LOCKS` 或新增 `_STEP_LOCKS`，在 `/v1/steps/write` 加 `async with`；或在 agent-runtime 侧把 `save_results` 改为顺序执行。
- 验收：1 round 并发 10 个工具全部写 step，`_index.jsonl` 行数恒等于 10，`seq` 无重复。

### P1-2 bridge 写路径强失败

- 当前：`create_scope/write_step/context_skill_begin` 全部 `except Exception: log + return empty`。
- 方案：写路径只捕获非重试类 `BusinessError` 返结构化错误，网络/5xx 抛出让 saga 重试。读路径保留软失败。

### P1-3/1-4 可观测性补强

- 加 `decide_rest` 结构化日志 + Cortex `skill_begin/end` 加 `log_cortex("skill.begun"/"skill.ended", ...)`。

### P1-6 context.read 幂等

- Cortex workspace 侧按 message `_idempotency_key` 去重；Runtime 侧生成稳定 idempotency_key。

### P1-10 rest 补偿兜底

- `saga_repo.mark_failed` 对 `subagent_rest` 本身失败时：记录告警 + 事件；可选 N 次指数退避后告警人工介入。

---

## Phase 2 — Architectural tightening（2-4 周）


| ID    | Status | Item                                                                  | 来源         |
| ----- | ------ | --------------------------------------------------------------------- | ---------- |
| P2-1  | `[x]`  | Cortex `advance_round` 改为服务端原子增                                       | Arch#1     |
| P2-2  | `[x]`  | 停用或合并 `/v1/internal/skill/`*，只保留有锁那一套                                 | Arch#1, #2 |
| P2-3  | `[x]`  | SQLite active stack projection 定单一权威来源，删除运行期文件遍历栈推断             | Arch#5     |
| P2-4  | `[x]`  | `/v1/scope/create` / `/v1/scope/end` 支持 idempotency key               | Arch#5     |
| P2-5  | `[x]`  | `skill_begin` 全局唯一索引（Bloom/hash-set in root meta）                     | Arch#7     |
| P2-6  | `[x]`  | `subagents.current_scope_id` 明确为非权威 UX 指针 or 删除                       | Arch#1     |
| P2-7  | `[x]`  | `Pydantic model_config extra='forbid'` + `internal-api-schemas.md` 对齐 | Arch#5     |
| P2-8  | `[x]`  | 修正 `cortex_bridge` HTTP 业务失败分类为 `BusinessError`（非 retryable）          | Arch#5     |
| P2-9  | `[x]`  | `business.get_subagents_due_for_wake` 补 `user_id`（避免 scheduler 静默丢弃）  | Arch#8     |
| P2-10 | `[x]`  | `chat_reply` 独立限频（不仅依赖 round cap）                                     | Arch#4     |


---

## Phase 3 — Platform & security（1-3 个月）


| ID    | Status | Item                                                                             | 来源         |
| ----- | ------ | -------------------------------------------------------------------------------- | ---------- |
| P3-1  | `[x]`  | Cortex 内部 HTTP 加 mTLS 或 `X-Internal-Secret` 必须校验                                 | Arch#8     |
| P3-2  | `[x]`  | Queue Service 加 HMAC / mTLS + 仅 loopback 绑定                                      | Arch#8     |
| P3-3  | `[x]`  | Gateway 按文档实现 Clerk JWKS RS256 + HS256 双栈                                        | Arch#8     |
| P3-4  | `[x]`  | 生产关闭 `TRUST_GATEWAY_X_USER_ID`                                                   | Arch#8     |
| P3-5  | `[x]`  | Cortex 单进程约束写入 `deployment-and-startup.md` + `uvicorn --workers 1` 启动检查          | Arch#2, #7 |
| P3-6  | `[x]`  | 分布式锁（Redis/DB）替换 `_SKILL_LOCKS`（为水平扩容准备）                                         | Arch#2     |
| P3-7  | `[x]`  | Prometheus 指标：`skills_begun/ended/archives/auto_closes/step_failures/lock_waits` | Arch#6     |
| P3-8  | `[x]`  | `/ready` 深度健康检查（store/OSS/bridge 连通性）                                            | Arch#6     |
| P3-9  | `[x]`  | `move_prefix` 原子性确认与文档化                                                          | Arch#7     |
| P3-10 | `[x]`  | `_budget_compact` 成本监控 + 阈值调优                                                    | Arch#7     |


---

## Invariants（要落到代码与文档的硬约束）

> **SSOT 已落档**：全部 10 条硬约束已整合到 [invariants.md](./invariants.md)，含代码锚点、强制级别、破坏后果。本表保留为索引。


| INV    | Status | 来源         | 说明                                                                                    |
| ------ | ------ | ---------- | ------------------------------------------------------------------------------------- |
| INV-1  | `[x]`  | Arch#1, #2 | 一个 root scope 内所有步骤写（steps/ + _index.jsonl）必须串行或原子追加                                  |
| INV-2  | `[x]`  | Arch#4     | `subagent_rest` 入口必须蕴含 `stack_depth == 0` 或 `force_rest_reason != none`               |
| INV-3  | `[x]`  | Arch#4     | 修改栈的工具（`skill_begin/end`）不并发执行                                                        |
| INV-4  | `[x]`  | Arch#5     | 权威 stack_depth = `/v1/context/status`（`CORTEX_CHECK_STACK`）                           |
| INV-5  | `[x]`  | Arch#5     | Cortex 业务校验失败返 `200 + ok:false`（非 4xx）                                                |
| INV-6  | `[x]`  | Arch#2, #7 | `_SKILL_LOCKS` key = `(user_id, agent_id, root_scope_id)`，仅在 is_root archive 成功时 drop |
| INV-7  | `[x]`  | Arch#7     | Cortex 以单进程运行，除非部署方提供分布式锁                                                             |
| INV-8  | `[x]`  | Arch#8     | 存储 key = `(user_id, agent_id, logical)`；`scope_id` 非全局 PK                             |
| INV-9  | `[x]`  | Arch#3     | Saga 重启安全：DAG step 的 idempotency_key 稳定                                               |
| INV-10 | `[x]`  | Arch#6     | `log_cortex` 在生产必须可用，禁用静默降级                                                           |


---

## Risk matrix（top 5）


| Rank | 风险                                    | 若不修会发生                                                          | 对应 ID       |
| ---- | ------------------------------------- | --------------------------------------------------------------- | ----------- |
| 1    | 并发 write_step 导致 `_index.jsonl` 丢失    | 历史文件遍历栈推断会读到陈旧 scope；现由 SQLite active stack projection 承担 LIFO 权威 | P1-1, INV-1 |
| 2    | write_step 静默失败                       | step 丢失但 saga 继续，历史残缺                                           | P0-2        |
| 3    | dispatch 竞态孤儿 saga                    | 监控上看到「saga started」但没有 active session                           | P0-3        |
| 4    | `_SKILL_LOCKS` 泄漏                     | 长时间运行后进程内存膨胀                                                    | P0-6        |
| 5    | react_think no-tool-after-retry 绕过栈检查 | Agent 带着未闭合 skill 进入 rest                                       | P0-5        |


---

## 非阻塞后续（已完成）


| ID    | Status | Item                             | 说明                                                                                                                                                                         |
| ----- | ------ | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OPT-1 | `[x]`  | FastAPI `on_event → lifespan` 迁移 | Cortex（`api.py` + `main_cortex.py`）、Queue Service（`queue_service/main.py`）全部切换到 `@asynccontextmanager lifespan`；去掉 DeprecationWarning。                                     |
| OPT-2 | `[x]`  | Cortex 自定义 logger 落盘             | `main_cortex.py` 在 `uvicorn.run` 前调用 `logging.basicConfig(level=INFO)`，单进程 / internal-key / sweeper 等诊断日志可见。                                                               |
| OPT-3 | `[x]`  | `RedisScopeLockManager` 真实实现     | `scope_locks.py` 新增 Redis 后端（`SET NX PX` + Lua release + heartbeat），`main_cortex.py` 通过 `CORTEX_LOCK_BACKEND=redis` 环境变量装载；7 个端点改走统一的 `_scope_lock_cm`，默认仍走 in-memory 零成本。 |


**启用 Redis 后端**：

```
CORTEX_LOCK_BACKEND=redis
CORTEX_REDIS_URL=redis://host:6379/0
CORTEX_REDIS_LOCK_TTL_SECONDS=300     # 可选，默认 300s
```

启用后 `_enforce_single_worker()` 自动放行，允许 `uvicorn --workers N` 或多副本部署；`/ready.scope_locks.backend` 字段反映当前后端。

---

## 维护规则

- 每完成一项：勾选 `[x]` + 在同一 commit 的 message 引用 `ID`（如 `fix(runtime): P0-2 write_step None→failure`）。
- 新发现的问题按 `P{phase}-{seq}` 续编，加入对应 Phase。
- 重大架构变动要更新同目录下的 `cortex-architecture.md` / `agent-runtime-all-topics.md` / `scope-lifecycle.md`。
