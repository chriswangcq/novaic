# PR-12 Preflight Review（HealthWorker → DispatchAssembler）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准** — 补完 §A 的 side-effect 声明 + §B/§C/§D 三处具体化后直接 T1 |
| 亮点 | `idempotency_key = f"health_fallback:{msgs[-1]['id']}"` 的设计是对的（Business 端 `order_by="timestamp ASC"` 保障了顺序） |

---

## §A（BLOCKER — 你漏记了一个大发现）当前 fallback 有 pre-existing 静默 bug，迁移正好修

### 事实链

1. `health_worker_sync.py:210` 现状：
   ```python
   saga_client.dispatch(
       agent_id=agent_id,
       subagent_id=f"main-{agent_id[:8]}",
       user_id="",                    # ← 硬编码空串
       trigger_type="user_message",
   )
   ```

2. Queue 端 `routes.py:513-517`：
   ```python
   if not (req.user_id or "").strip():
       raise HTTPException(
           status_code=400,
           detail="user_id is required to dispatch a wake (Meta skill auto-open needs it).",
       )
   ```

3. Business 端 `/internal/messages/unread-grouped` (`message.py:242-248`) 的 projection 里**根本没有 `user_id`**，所以 HealthWorker 的本地数据也拿不到 user_id。

**结论**：`_scan_unhandled_messages` 的 fallback dispatch **一直被 Queue 400 拒绝**。日志里静静打一条 `Fallback dispatch failed for {agent_id}: ...`（`:215` warning 级别），然后就没了。**这个兜底机制实际上一年多没兜住任何东西**。

### 为什么 PR-12 自动修了这个 bug

`DispatchAssembler.assemble(agent_id)` 内部调 `resolver.resolve(agent_id)` → Business `/internal/agents/{agent_id}/owner` → 返回 `user_id`。Assembler **自己会查到正确的 user_id**。Queue 400 拒绝路径消失。

### 返工要求

preflight §3 补一章或 §5 追加一段，明文声明：

> **本 PR 附带修复 pre-existing 静默 bug**：现行 `_scan_unhandled_messages` 硬编码 `user_id=""` 触发 Queue 400，fallback 实际从未成功派发过任何消息。PR-12 迁移到 Assembler 后，`resolver.resolve(agent_id)` 自动补齐 user_id，fallback 第一次真正工作。
>
> 风险提示：这意味着此前积压的 orphan messages 在 PR-12 上线后会**首次被批量触发唤醒**。老板需要在生产上线时预判可能的 dispatch 流量尖峰。建议上线第一天由运维关注 `dispatch_total{trigger=user_message, caller=runtime-health}` 的峰值。

同时：
- 在 `technical-debt.md` 加一条"已修复"记录（可选用删除线标注），说明此 bug 及其修复 PR 编号。
- 单测里加一条 `test_assembler_called_with_resolver` 或类似：确认 HealthWorker 调 Assembler 时**没有**直接传 `user_id`，而是让 Assembler 从 resolver 查（mock resolver 的 `resolve` 被调用一次）。

### 关于上线流量尖峰，你再做一件事

在 PR-12 `_scan_unhandled_messages` 迁移后，**加一个"批次上限"保护**：

```python
MAX_FALLBACK_PER_TICK = 50   # 或从配置读
for idx, (agent_id, msgs) in enumerate(messages_by_agent.items()):
    if idx >= MAX_FALLBACK_PER_TICK:
        logger.warning("event=health_fallback_capped pending_agents=%d", len(messages_by_agent) - idx)
        break
    ...
```

因为这个兜底第一次真的启动时，可能一次性要处理大量历史 orphan。分批释放，下一个 tick 继续。这是保护 Queue 不被打爆的必备动作。preflight §3 加上这一条。

## §B（事实引用必须补）你 §3 的 idempotency 设计是对的但没举证

`msgs[-1]["id"]` 假设 `msgs` 有序。**Business 端 `message.py:232` `order_by="timestamp ASC"` 保障了这点**，你的设计 sound。

但 preflight §3 要把这条引用加上：

> 订单性保障：Business `/internal/messages/unread-grouped` 在 `novaic-business/business/internal/message.py:232` 使用 `order_by="timestamp ASC"`，同一 agent 的 msgs 按时间升序返回，故 `msgs[-1]` 稳定指向最新一条消息。

否则后人读不懂为什么你敢这么用 `[-1]`。

## §C（必做）async 化覆盖：`/recover/all` 也必须改 async

preflight §4 说把 `_perform_check` async 化。但 `_perform_check:137` 的 `client.post("/api/queue/recover/all", ...)` 用的是 **sync** `internal_client`（:81 已明文 `from common.http.clients import internal_client`）。

async 函数里调 sync HTTP 会**堵塞整个事件循环**——跟 PR-10 的教训同款，不同形态。

必须：
- `_get_client()` 改成返回 `httpx.AsyncClient`（用 `internal_async_client`）
- `_perform_check` 里 `await client.post(...)`、`await queue_client.get(...)`（sessions 查询那里）
- `finally` 里 `await self._client.aclose()`（AsyncClient 的 close 是 async）

preflight §4 明文把这几处列出来，不要只说 "`time.sleep` → `asyncio.sleep`"。

另外 preflight §4 有**笔误**：说要 async 化 `_check_and_wake`——那是 Scheduler 的方法名，HealthWorker 里叫 `_perform_check` 和 `_scan_unhandled_messages`。改对。

## §D（必做）§6 CI allowlist 动作描述模糊，钉死

PR-12 完成后：
- `scheduler_worker_sync.py`（PR-13 已做）+ `health_worker_sync.py`（本 PR）**都不再调用** `SagaClient.dispatch()`
- 我 grep 了 `saga_client\.dispatch|\.dispatch\(.*trigger_type` 整个 runtime，**`health_worker_sync.py:207` 是最后一个调用方**

所以 **PR-12 本 PR 里必须做两件事**（而不是"可选移除"）：

1. **删除 `task_queue/client.py` 里 `SagaClient.dispatch()` 方法**（以及它不再被用到的相关 helper），这样 `/api/queue/dispatch` 字符串从文件里消失
2. **从 `scripts/ci/lint_dispatch.sh` allowlist 删除 `task_queue/client.py` 条目**，并把"TRANSITIONAL — remove after PR-12/PR-13" 注释一起清掉

preflight §6 改成这种精确说法，不是 "应当彻底将 SagaClient 移除（或只移除其中的 dispatch 遗留）" —— 语气必须明确执行"或"的哪一个：**执行"只移除 dispatch 方法"**（SagaClient 类如果还有别的公用方法就留着）。

顺手做一次 `rg 'SagaClient\b' novaic-agent-runtime/` 看 SagaClient 还剩什么用途，preflight 里列清楚，T1 实现时避免误删。

## §E（nice-to-have，不 block）

### E.1 Metrics 补一个 `fallback_dispatched`
现有 `HealthWorkerMetrics` 没有 `fallback_dispatched` 字段。`_scan_unhandled_messages:202` 有 local `dispatched = 0` counter 但没导出。**加一个字段**：
```python
@dataclass
class HealthWorkerMetrics:
    ...
    fallback_dispatched: int = 0
```
并在 tick 结束时 `self.metrics.fallback_dispatched += dispatched`。这样 §A 说的"首次真正工作"的流量可观测。

### E.2 日志用 logger 不用 print
跟 PR-13 §E.1 同理。新结构化日志 (`event=health_fallback ...`) 用 `logger.info/error`，原有 `_log` 保留避免 diff 爆炸。

---

## 返工 Checklist

- [ ] §A 补 "pre-existing bug 修复" 声明 + 生产流量尖峰风险提示 + 批次上限 `MAX_FALLBACK_PER_TICK` 保护 + `test_assembler_called_with_resolver` 单测
- [ ] §B 引用 `message.py:232` `order_by="timestamp ASC"` 作为 idempotency 有序性证据
- [ ] §C `_get_client` 改 `internal_async_client` / `aclose` / `await client.post` 全覆盖 + 改正 `_check_and_wake` 笔误
- [ ] §D allowlist 和 `SagaClient.dispatch` 删除动作确定为"**删 dispatch 方法 + 删 allowlist 条目**"（不是二选一）+ preflight 列清 SagaClient 其他用途
- [ ] §E.1 `fallback_dispatched` metric 加字段
- [ ] §E.2 `logger` 使用方式说明

修完直接 T1。PR-12 完成后 M1 （上游 dispatch 完全收敛）才算真正达成——所以这次每个勾都要对得起。
