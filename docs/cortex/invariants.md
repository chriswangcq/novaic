# Cortex + Agent Runtime — Invariants（硬约束清单）

> **单一真相源（SSOT）**。本文是 Cortex 与 Agent Runtime 架构必须保持的**硬约束**集合。任何重构、扩容、引入新模块时都必须回读本页，确保**没有一条被打破**。
>
> 约束来源：[architecture-review-2026-04-17.md](./architecture-review-2026-04-17.md) 的 8 位架构师评审；落地追踪见 [hardening-checklist.md](./hardening-checklist.md)。
>
> 符号：
> - `[CODE]` 已在代码中强制（startup 断言、HTTP 中间件、或 async lock 结构化保证）。
> - `[CONTRACT]` 靠调用方遵守 + 代码注释 + 评审拦截，未强制检查。
> - `[PROD-ONLY]` 仅生产环境必须，开发态允许降级。

---

## 总览

| INV | 类别 | Status | 强制级别 | 主要落点 |
| --- | --- | --- | --- | --- |
| INV-1 | 写入并发 | ✅ | `[CODE]` | `api.py::_get_scope_lock` / `/v1/steps/write` |
| INV-2 | 生命周期 | ✅ | `[CONTRACT]` | `react_actions._decide_rest_or_continue` + `subagent_rest` |
| INV-3 | 栈并发 | ✅ | `[CODE]` | `api.py::_get_skill_lock`（= `_get_scope_lock` 别名） |
| INV-4 | 权威读 | ✅ | `[CONTRACT]` | `CORTEX_CHECK_STACK` 走 `/v1/context/status` |
| INV-5 | 错误分类 | ✅ | `[CONTRACT]` | Cortex 业务失败 = `200 {ok:false}`；5xx = 重试 |
| INV-6 | 锁 key | ✅ | `[CODE]` | `_SCOPE_LOCKS` key = `(user_id, agent_id, scope_id)` |
| INV-7 | 部署拓扑 | ✅ | `[CODE]` + `[PROD-ONLY]` | `main_cortex._enforce_single_worker` |
| INV-8 | 存储 key | ✅ | `[CONTRACT]` | `storage-and-keys.md` §2 |
| INV-9 | Saga 重放 | ✅ | `[CODE]` | `context_handlers.seen_keys` 去重 |
| INV-10 | 可观测性 | ✅ | `[CODE]` + `[PROD-ONLY]` | `observability.log_cortex` 强制导入 |

---

## INV-1 · 步骤写入串行化（per-root）

> 同一 root scope 内的所有 step 写入（`steps/NNNN_*` + `_index.jsonl` 追加）必须**串行或原子追加**，不得出现 RMW 并发。

**动机**：
- `write_step` = `_count_step_dirs` + `_sys_append_line` 是 Read-Modify-Write。
- 并发执行会导致 `seq` 重复 / `_index.jsonl` 行丢失 / `resolve_active_scope_path` 读到陈旧 scope → LIFO 错乱。

**落地**：

```447:450:novaic-cortex/novaic_cortex/api.py
@app.post("/v1/steps/write")
async def steps_write(req: StepWriteRequest):
    lock = await _get_scope_lock(req.user_id, req.agent_id, req.scope_id)
    async with _instrumented_scope_lock(lock, op="steps_write"):
```

所有 step 写入（包括 react_actions 的 `save_results` 并发分支）走同一把 per-root lock。

**破坏后果**：P0-2 + P1-1 所描述：saga 假阳性成功 + 历史残缺 + 栈推断错误。

**反例（禁止）**：绕过 `/v1/steps/write` 直接调 `workspace.write_step`、多 worker 进程共写同一 bucket（见 INV-7）。

---

## INV-2 · `subagent_rest` 入口前提

> 进入 `subagent_rest` saga 的任何一次调用，**必须**蕴含以下之一：
> - `stack_depth == 0`（栈已清空，合法 idle）
> - `force_rest_reason != none`（被显式强制休眠，已接受栈上挂起作为代价）

**动机**：Agent 带着未闭合 skill 进入 rest → 下次 wake 看到残留栈 → LIFO 检查报错或产生孤儿子 scope。

**落地**：

```x:y:novaic-agent-runtime/task_queue/sagas/react_actions.py
# _decide_rest_or_continue 在 rest 分支前读取 CORTEX_CHECK_STACK 的 stack_depth + stack_known。
# stack_known=False 时禁止 rest；stack_depth>0 时只在 force_rest_reason 存在时允许。
```

+ P1-5 后 `subagent_rest` 强制携带 `rest_reason` 与 `round_num`，便于事后审计（见 [handlers/cortex_handlers.py](./agent-runtime-all-topics.md) 对应段落）。

**破坏后果**：P0-5 所描述 no-tool-after-retry 直通 rest 的 bug。

---

## INV-3 · 栈修改工具不并发

> `skill_begin` / `skill_end` / `scope_end` / `advance_round` / `counter_inc` / `context_append` / `steps_write` **不得**在同一 root scope 内并发执行。

**落地**：全部走同一把 `_get_scope_lock` / `_get_skill_lock`（二者是别名，共享 `_SCOPE_LOCKS` 池）：

```562:566:novaic-cortex/novaic_cortex/api.py
lock = await _get_skill_lock(req.user_id, req.agent_id, req.scope_id)
async with _instrumented_scope_lock(lock, op="skill_begin"):
```

**破坏后果**：栈 LIFO 顺序错乱、scope_ids 索引冲突、round_num 丢失更新。

**配套**：INV-6（锁 key 语义）、INV-7（单进程约束）。

---

## INV-4 · 权威 `stack_depth` 读取路径

> 任何决策用途的 `stack_depth`，**只**能来自 `/v1/context/status`（即 Runtime 的 `CORTEX_CHECK_STACK` topic）。

**动机**：
- `subagents.current_scope_id`（业务库字段）是 **UX 指针**，允许滞后 / 为 None（见 P2-6）。
- `ContextEngine` 内部的瞬态栈快照在多次请求间不保证一致。
- 只有 `/v1/context/status` 会走 `_collect_active_stack`，从文件系统 `/ro/active/` 重建权威结果（P2-3）。

**落地**：

```:novaic-cortex/novaic_cortex/api.py
# /v1/context/status 调用 _collect_active_stack；
# 返回 stack_depth + frames（scope_id, skill, depth）供 Runtime 决策。
```

Runtime 侧 `handle_cortex_check_stack` 在异常时返 `stack_depth=1, stack_known=False`，`_decide_rest_or_continue` 看到 `stack_known=False` 不得 rest（INV-2 配合）。

**破坏后果**：绕过 status 读业务库快照 → 决策基于陈旧数据 → 假 rest / 假 continue。

---

## INV-5 · Cortex 业务校验失败 = `200 {ok:false}`

> Cortex 的**业务层校验失败**（如 skill 不存在、stack 已满、scope 已归档）必须返 `HTTP 200 {ok: false, error: ...}`，**不得**返 4xx。4xx 只用于参数格式错误、路由不存在、认证失败。

**动机**：
- 5xx = 可重试（网络、超时、进程崩溃）。
- 业务失败如果返 4xx，saga 会 retry 到 max 次，浪费 LLM 调用且时间线重复污染。
- 返 `200 {ok:false}` 由 `cortex_bridge` 翻译为 `BusinessError`（P2-8），在 saga DAG 里走 compensation 而非 retry。

**落地**：Cortex 侧见 `api.py` 中所有 `return {"ok": False, "error": ...}` 分支（line 575+）；Runtime 侧见 `cortex_handlers.py` raise `BusinessError`。

**破坏后果**：saga 无休止 retry / compensation 路径被跳过。

---

## INV-6 · `_SCOPE_LOCKS` key 语义

> 锁 key = `(user_id, agent_id, scope_id)`，**必须**三元组齐全；scope_id 是 root scope（子 scope 的操作通过 `resolve_active_scope_path` 归一到 root 后再取锁）。

**落地**：

```51:55:novaic-cortex/novaic_cortex/api.py
_SCOPE_LOCKS: dict[tuple[str, str, str], asyncio.Lock] = {}
_SCOPE_LOCKS_GUARD = asyncio.Lock()

_SKILL_LOCKS = _SCOPE_LOCKS
```

```96:101:novaic-cortex/novaic_cortex/api.py
async def _drop_scope_lock(user_id: str, agent_id: str, scope_id: str) -> None:
    key = (user_id, agent_id, scope_id)
    async with _SCOPE_LOCKS_GUARD:
        _SCOPE_LOCKS.pop(key, None)
```

**清理时机**：仅当 `scope_end` 成功归档 root scope 时 drop（P0-4 + P2-4 保证归档幂等）。

**破坏后果**：
- 只用 `scope_id` 做 key → 跨用户 UUID 碰撞时锁混淆（P0-7）。
- 不 drop → 长运行泄漏（P0-6，尚未完全修复）。

---

## INV-7 · Cortex 单进程运行

> Cortex HTTP 服务**必须**以 `uvicorn --workers 1` 运行，除非部署方提供了分布式锁替代 `_SCOPE_LOCKS`（见 [scope_locks.py](../../novaic-cortex/novaic_cortex/scope_locks.py) 的 `ScopeLockManager` 协议，P3-6）。

**动机**：
- `_SCOPE_LOCKS` 是 `asyncio.Lock`，**进程内**语义。多 worker 时每个 worker 有独立锁池，INV-1/3 全部失效。
- 水平扩容必须先切到分布式后端（Redis `SET NX PX` / DB row lock），才能 `workers > 1` 或跨机部署。

**落地**（startup 断言）：

```25:43:novaic-cortex/novaic_cortex/main_cortex.py
def _enforce_single_worker() -> None:
    raw_workers = (os.environ.get("UVICORN_WORKERS") or "").strip()
    if raw_workers:
        try:
            n = int(raw_workers)
        except ValueError:
            n = 1
        if n > 1:
            raise RuntimeError(...)
```

配套文档：[deployment-and-startup.md](./deployment-and-startup.md) §单进程约束。

**破坏后果**：silent data corruption（不同 worker 同时 append `_index.jsonl`）。

---

## INV-8 · 存储 key 三元组

> 所有 OSS 对象 key 的前缀必须是 `(user_id, agent_id, logical_path)` 三元组；`scope_id` **不是**全局主键，跨 (user, agent) 不保证唯一。

**动机**：
- Cortex 按 `WorkspaceRegistry.get(user_id, agent_id)` 拿 scoped store；任何绕过 registry 直接拼 `scope_id` 的地方都会有跨租户泄漏或 UUID 碰撞。
- P0-7 要求 `cortex_bridge` 缓存 key 升级为 `(scope_id, user_id, agent_id)` 来覆盖复合语义。

**落地**：详见 [storage-and-keys.md](./storage-and-keys.md) §2 对象键结构。所有 `workspace.py` 方法都在 `(user_id, agent_id)` 隔离域内操作。

**破坏后果**：A 用户的消息泄漏到 B 用户的 scope、或跨用户 skill_begin 判重失效。

---

## INV-9 · Saga 重放安全

> Saga 中每一步（DAG node）必须是**幂等**的。重试同一 step 不得产生重复副作用：
> - `context.read` → 同一 `_idempotency_key` 不得重复 append。
> - `skill_begin` / `scope_create` → 同 `scope_id` 二次创建直接返回既有 meta（P2-4）。
> - `skill_end` / `scope_end` → 已归档状态下返成功（幂等归档）。
> - `write_step` → Cortex 侧负责 seq 分配，Runtime 侧按内容计算 step_hash 作为 idempotency（P1-6）。

**落地**（context.read 去重示例）：

```40:102:novaic-agent-runtime/task_queue/handlers/context_handlers.py
seen_keys: set[str] = set()
for m in existing_messages:
    key = m.get("_idempotency_key") if isinstance(m, dict) else None
    if key:
        seen_keys.add(key)
# ...
if idem_key in seen_keys:
    continue
```

**破坏后果**：saga 重启 / 重试时时间线出现重复 user/tool/assistant 消息，context 膨胀。

---

## INV-10 · `log_cortex` 必须可用

> 生产环境中 `log_cortex` **不得**静默降级。所有关键事件（`skill.begun`、`skill.ended`、`scope.archived`、`scope.auto_closed_children`、`step.write_failed`、`skill.begin_rejected`）必须能够落到结构化日志 **并且** 同时更新 Prometheus 计数器。

**动机**：
- 可观测性是 Cortex 状态真相的外化。没有日志 → 运维无法判断是否触发了 auto_close、是否超深、是否被 rate-limit 拒绝。
- P1-9 之前 `workspace.py` / `api.py` 里有 `try/except ImportError: log_cortex = noop`，这在部署失误漏装 observability 时会静默吃掉事件。

**落地**：
- `workspace.py` / `api.py` 已移除 `try/except ImportError` fallback（P1-9 + P1-3）。
- `observability.py::log_cortex` 中 6 个关键 event 直接调用 `metric_inc`（P3-7）。
- `/metrics` 端点以 Prometheus text format 暴露（P3-7）。
- Cortex 启动时若 `observability` import 失败 → 直接 crash（INV-10 `[CODE]` 级强制）。

**破坏后果**：事后无法复现 bug、无法告警、无法统计 auto_close 率。

---

## 修改本文的规则

1. 新增 INV 时按 `INV-{N+1}` 续编，在「总览」和正文同时添加，**绝不复用已退役编号**。
2. 任何 PR 若需要**弱化**某条 INV，必须：
   - 在 PR 描述明确说明**为什么**要弱化（性能 / 紧急 hotfix / 新架构）；
   - 把对应 `[CODE]` 降级到 `[CONTRACT]` 需要同时补注释 + checklist 新增追踪项；
   - 把 `[CONTRACT]` 移除前必须在 [hardening-checklist.md](./hardening-checklist.md) 开一个 Phase N+1 跟踪项，确认已经不存在任何调用方依赖该约束。
3. 发现新的、未被本文覆盖的硬约束时，优先写进本文再开 hardening item，避免散落在各 module 注释里。
