# PR-12 Preflight Review (Health Worker to Assembler)

## 1. 修改范围
- `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`
- `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py` (复用 PR-13 创建的 factory)

## 2. 穷举 call site 与 TriggerType 多态
通过 `rg '\.dispatch\('` 扫描 `health_worker_sync.py` 发现：
- 唯一的一处 call site 在 line 207 `saga_client.dispatch(...)`
- 目前代码中 **写死了 `trigger_type="user_message"`**
- 这是因为 `messages_by_agent` 的来源是 `/internal/messages/unread-grouped`，而 Business 侧该接口内部写死了 `filters={"read": 0, "type": "USER_MESSAGE"}`，因此 HealthWorker 兜底扫描当前只会触达 User Message 漏派发的情况。

**映射表：**
| 原先 Raw String | 新版 `TriggerType` | 说明 |
| --- | --- | --- |
| `"user_message"` | `TriggerType.USER_MESSAGE` | 当前唯一的漏处理触发源 |

## 2.5 意外发现：隐蔽的 user_id 空置 Bug (Blocker)
- 现有的 `saga_client.dispatch` 写死了 `user_id=""`。
- 而 Queue 端的 `/dispatch` 接口明确校验了 `if not req.user_id.strip(): raise HTTPException(400)`。
- 这意味着 **HealthWorker 的 fallback 一年多来从未真正成功派发过任何消息**！全都静默 400 失败了。
- 本次接入 Assembler，因为 Assembler 内置了 `AgentOwnershipResolver` 会自动查出真实的 `user_id`，这会导致积压的历史 orphan messages 瞬间被唤醒。
- **应对方案**：
  1. 在 `_scan_unhandled_messages` 循环中加入 `MAX_FALLBACK_PER_TICK = 50` 保护。超出限制时记录 `logger.warning("event=health_fallback_capped")` 并 break。
  2. 在单测中验证：`health_worker` 没有自己传 `user_id`，而是依靠 Assembler 解析。
  3. 登记到 `technical-debt.md`。

## 3. Crash Recovery 语义与幂等键 (idempotency_key) 分析
HealthWorker 包含两层恢复机制：
1. **进程崩溃导致已建的 Saga 卡死**：由 `POST /api/queue/recover/all` 处理。该接口内部调用 `orchestrator.recover_stale()`，它会直接将 SQLite 中的 saga 状态重置为 `pending`，由 Saga Worker 继续执行。这层机制**不涉及**新 dispatch。
2. **Gateway 崩溃导致消息入库但未建 Saga**：由 `_scan_unhandled_messages()` 负责兜底。当前代码中：
   - 过滤了已经在 `active_sessions` 中的 agent，避免重复派发。
   - 但是 **当前并未传递 `idempotency_key`**！这意味着如果连续执行两次 dispatch，而恰巧 Queue 没能及时把该 agent 放入 session，可能会重复派发。

**结合 `session_repo.py` 分析：**
- Queue 侧如果遇到相同的 `idempotency_key`，会直接查找历史 saga 并返回 `action: deduped`，而**不会**创建新 saga。
- 对于因为 Gateway 崩掉而漏创建 Saga 的消息，它根本不存在历史 Saga。我们需要给它一个唯一的幂等键以防止 HealthWorker 重复派发。
- **方案**：因为 `msgs` 是依据 `message.py:232` 中的 `order_by="timestamp ASC"` 返回的，我们可以使用 `idempotency_key = f"health_fallback:{msgs[-1]['id']}"`（取最后一条消息的 ID），这保证了同一批漏掉的消息只会触发一次兜底唤醒。同时，如果该 Saga 随后崩溃，机制 1 会将其拉起，不依赖机制 2。另外还要把 `message_ids=[m['id'] for m in msgs]` 放进 `metadata` 里。

## 4. 上下文提升 (Sync to Async)
参考 PR-13 的手法：
- 替换 `time.sleep` 为 `await asyncio.sleep`。
- 将 `run`，`_perform_check`，以及 `_scan_unhandled_messages` 全部提升为 `async def`。
- `internal_client` 必须替换为 `internal_async_client` (或 httpx.AsyncClient)，并在所有调用处 `await` 以防止阻塞事件循环。
- `finally` 中使用 `await self._client.aclose()`。
- 入口 `start_worker()` 与 `__main__` 下面统一用 `asyncio.run(worker.run())` 顶层包覆。

## 5. 日志与异常处理
- 在 `HealthWorkerMetrics` 添加 `fallback_dispatched: int = 0`。
- 使用 `get_assembler()` 获取单例 `DispatchAssembler` (注入 service_name="runtime-health")。
- 在 fallback dispatch 成功时记录 `logger.info("event=health_fallback agent=%s messages=%d result=ok action=%s saga_id=%s")`
- 异常分为 `no_owner`, `queue_4xx` (Error 跳过), 以及 `queue_5xx` (Error 留待重试)。

## 6. CI 准入清理
- 本修改后，将彻底废弃 `SagaClient.dispatch`，并从 `task_queue/client.py` 中删除它。
- 随后从 `scripts/ci/lint_dispatch.sh` 的 `ALLOWLIST` 彻底删掉 `task_queue/client.py` 及其相关的 transitional comment。
