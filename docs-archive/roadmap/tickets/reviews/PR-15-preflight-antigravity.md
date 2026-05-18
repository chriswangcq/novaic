# PR-15 Preflight 分析：Dispatch Subscriber 骨架

本预案聚焦于 PR-15 阶段所引入的 outbox subscriber 骨架搭建，严格遵循“只做骨架、零副作用、无具体消费逻辑”的范围约束。涉及到读路径与消费语义的复杂设计将延后至 PR-16 进行决策。

## 架构决策与修正

### 1. 部署位置：Business 进程内的协程 Worker
**结论**：部署在 `novaic-business` 中，随 FastAPI lifespan 启停。
- **现实验证**：Business 的 `main_business.py` 已经在使用 `@asynccontextmanager lifespan` 管理生命周期。
- **获取依赖**：摒弃错误的 `app.state.assembler` 设想。在 PR-11 中已经确立了 `get_assembler()` 模块单例模式，Lifespan 将通过工厂函数获取 Assembler 并注入 Subscriber 骨架中。
- **惰性引入 (Lazy Import)**：为了保证 `DISPATCH_SUBSCRIBER_ENABLED=0` 时绝对的**零副作用**，所有的 import（包括 `get_assembler` 和 `DispatchSubscriber` 类本身）都将放在 `if SUBSCRIBER_ENABLED:` 分支内进行，确保关闭时甚至连 Class 都不会被加载进 `sys.modules`。

### 2. 读路径抽象延后到 PR-16
**结论**：PR-15 的 `DispatchSubscriber.__init__` **不接 `db` 依赖**，只接 `assembler` 和轮询参数。
由于 Business 与 Entangled 是两个独立的进程，Business 并没有操作 Entangled 数据库的直接句柄。PR-15 的 `_tick()` 将固定返回 0，无需进行任何数据库交互。

至于具体如何读取 outbox 行，将在 PR-16 的 preflight 中详细决策以下子问题：
1. 是否新增 HTTP 端点（方案 A）还是将 subscriber 搬入 Entangled 内部协程（方案 B）。
2. claim/release/mark_delivered 的原子性保证手段。
3. 多个 Worker 副本的 fencing 语义抢占模型。

### 3. Worker ID 格式优化
**结论**：虽然骨架阶段暂不进行消费认领，但为了规避在 Kubernetes 等容器化部署下可能遇到的 `hostname` 相同冲突问题，初始化的 `worker_id` 将采用严谨的组合格式：`f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"`。

### 4. 双发并发语义 (对齐结论)
**结论**：在 PR-17 切流前，inline dispatch 和 subscriber 必定会同时触发相同的消息。得益于 PR-14 我们对 `idempotency_key="msg:{id}"` 的对齐，Queue 的去重机制将成为绝对的防双发屏障，这为 PR-15/16 阶段提供了安全的 Canary 并行前提。

---

## 测试与验收设计 (T1 行动指南)

### 单测骨架：模拟无限循环启停
为了证明 `_tick()` 为 0 时的平稳休眠和安全退出机制，在 `tests/` 中添加单测：
```python
import asyncio
import pytest
from unittest.mock import AsyncMock
from business.subscribers.dispatch_subscriber import DispatchSubscriber

@pytest.mark.asyncio
async def test_subscriber_tick_zero_sleeps_and_stops():
    mock_assembler = AsyncMock()
    # 极短的 poll interval 以加快测试周期
    sub = DispatchSubscriber(assembler=mock_assembler, poll_interval=0.01)
    task = asyncio.create_task(sub.run())
    
    await asyncio.sleep(0.05) # 让循环 tick 几次空转
    
    sub.stop()
    try:
        await asyncio.wait_for(task, timeout=1.0)
    except asyncio.TimeoutError:
        pytest.fail("Subscriber did not stop gracefully upon stop() signal")
    
    # 确保证明零副作用 (空转)
    mock_assembler.assemble_and_dispatch.assert_not_called()
```

### 集成验证 (E2E Stdout 捕获)
在实际的终端中执行带有和不带有 `DISPATCH_SUBSCRIBER_ENABLED` 环境变量的 `scripts/start.sh` 命令。使用 `grep` 提取真正的业务启动日志，将其粘贴至 T1 报告中。以此来提供最严谨的“零副作用”和“正确挂载”的真实验收证据，坚决不打空勾。

---
**本预案修订完毕，所有 Blockers 已被处理。** 立即进入 T1 执行阶段。

## T1 实施与集成验证记录

```text
--- Running with DISPATCH_SUBSCRIBER_ENABLED=0 ---
2026-04-18 16:57:28,431 [INFO] business: dispatch_subscriber disabled (DISPATCH_SUBSCRIBER_ENABLED=0)

--- Running with DISPATCH_SUBSCRIBER_ENABLED=1 ---
2026-04-18 16:58:16,888 [INFO] business: dispatch_subscriber enabled worker_id=ChrisMacBook-Pro.local:25671:f899849e
2026-04-18 16:58:16,889 [INFO] business.subscribers.dispatch_subscriber: dispatch_subscriber starting worker_id=ChrisMacBook-Pro.local:25671:f899849e
```
