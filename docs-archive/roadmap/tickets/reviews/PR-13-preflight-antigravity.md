# PR-13 Preflight Review (Scheduler Worker to Assembler)

## 1. 修改范围
- `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py`
- `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py` (新增隔离的 factory)
- `novaic-common/common/wake/assembler.py` (补充支持 `idempotency_key`)

## 2. 穷举 `/dispatch` 调用点
在 `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py` 中，调用点只有一处，是通过 `SagaClient` 的封装触发的：
```python
# scheduler_worker_sync.py:160
                    result = self.saga_client.dispatch(
                        agent_id=agent_id,
                        subagent_id=subagent_id,
                        user_id=user_id,
                        trigger_type="scheduled_wake",
                        metadata=metadata,
                        idempotency_key=idempotency_key,
                    )
```

## 3. TriggerType 映射与幂等键透传 (Blocker 提前预判)
- **映射**：原有的 `"scheduled_wake"` 完美映射到 `TriggerType.SCHEDULED_WAKE`。
- **缺失的参数支持**：原生的 Queue `/dispatch` 接受 `idempotency_key`（并且 Scheduler 依赖它做了避免同一时间多次唤醒的幂等）。但目前 `novaic-common/common/wake/assembler.py` 中 `DispatchRequest` 和 `assemble_and_dispatch` 均未定义此字段。
- **解决**：本 PR 需要在 `Assembler` 内部补全 `idempotency_key: str | None = None`，并将其加入 `to_queue_payload()` 透传给 Queue Service。

## 4. 上下文提升 (Sync to Async)
按照“上升成 async”的手法：
- `_check_and_wake` 变为 `async def`，并在内部直接 `await assembler.assemble_and_dispatch(...)`。
- 主循环 `run(self)` 变为 `async def run(self)`，并将轮询延时由 `time.sleep` 变为 `await asyncio.sleep(self.check_interval)`。
- 最外层的入口函数 `start_worker` 使用 `asyncio.run(worker.run())` 启动。因为这是个独立的轮询 Worker 进程/线程，所以不会与已有的事件循环冲突，完美实现无缝异步化。

## 5. Assembler Factory (隔离)
- 放置于 `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py`。
- 通过 `os.environ.get("BUSINESS_URL")` 等注入 `AgentOwnershipResolver`。
- 注入 `service_name="runtime-scheduler"`，彻底不混用 Business 的配置。

## 6. 日志处理与 Error 处理
在 `_check_and_wake` 内部捕获 `DispatchError` 并分类处理：
- 结构化日志：`event=scheduled_wake agent=... due_at=... result=ok|no_owner|queue_400|network...`
- `no_owner` 或 `queue_400` → `level="error"` 并跳过该 agent（因为属于业务逻辑/配置断层）。
- `queue_5xx` / `network` → `level="error"` 并保留原逻辑跳过（下一个 tick 自然会再拉取重试）。
- `ok` → 根据 `result.buffered` 或 `result.raw.get("action")` 判断是启动新 saga 还是被 buffer，如实记录。

## 7. 测试策略
- 写 mock test (类似 PR-11)：
  - `patch("task_queue.workers.wake.assembler_factory.get_assembler")`
  - 触发 `_check_and_wake`（提供模拟的 `due_agents` 列表）。
  - Assert `assembler.assemble_and_dispatch` 被调用，并确认 `TriggerType.SCHEDULED_WAKE`、`metadata`、`idempotency_key` 悉数传对。

## 8. CI 准入清理
完成代码后，进入 `scripts/ci/lint_dispatch.sh` 中删除 `ALLOWLIST` 里的 `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py` 相关行，确保拦截生效。
