# PR-15  `dispatch_subscriber` 骨架（默认 flag=off）

| 字段 | 值 |
| --- | --- |
| **Phase** | 2 |
| **Milestone** | M2 |
| **承诺** | R6 |
| **Status** | `[ ]` |
| **Depends on** | PR-10, PR-14 |
| **Blocks** | PR-16 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(business): dispatch_subscriber skeleton (disabled by default)` |

## 目标

把 subscriber 进程/协程骨架落地 + 启停 flag；**默认不启动**，给 PR-16 留出实现空间而不影响生产。

## 范围

- `novaic-business/business/subscribers/__init__.py`（新建子包）
- `novaic-business/business/subscribers/dispatch_subscriber.py`
- `novaic-business/main_business.py`（启动挂载）
- 环境变量 / CLI flag：`DISPATCH_SUBSCRIBER_ENABLED` (default `0`)

## 前置 Checklist

- [ ] PR-10 合并，Assembler 可用
- [ ] PR-14 合并，outbox 表存在

## 实施 Checklist

### 骨架

```python
# business/subscribers/dispatch_subscriber.py
class DispatchSubscriber:
    def __init__(self, db, assembler, *, poll_interval=0.5, batch_size=50, worker_id=None):
        self.db = db
        self.assembler = assembler
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.worker_id = worker_id or socket.gethostname()
        self._stop = asyncio.Event()

    async def run(self):
        logger.info("dispatch_subscriber starting worker_id=%s", self.worker_id)
        while not self._stop.is_set():
            try:
                n = await self._tick()
                if n == 0:
                    await asyncio.wait_for(self._stop.wait(), timeout=self.poll_interval)
            except asyncio.TimeoutError:
                continue
            except Exception:
                logger.exception("subscriber tick crashed; sleeping")
                await asyncio.sleep(1)

    async def _tick(self) -> int:
        return 0                # PR-16 填充真实逻辑

    def stop(self):
        self._stop.set()
```

### 挂载

```python
# main_business.py
SUBSCRIBER_ENABLED = os.environ.get("DISPATCH_SUBSCRIBER_ENABLED", "0") == "1"

@asynccontextmanager
async def lifespan(app):
    if SUBSCRIBER_ENABLED:
        sub = DispatchSubscriber(db=..., assembler=app.state.assembler)
        task = asyncio.create_task(sub.run())
        app.state.subscriber = sub
        logger.info("dispatch_subscriber enabled")
    else:
        logger.info("dispatch_subscriber disabled (DISPATCH_SUBSCRIBER_ENABLED=0)")
    try:
        yield
    finally:
        if SUBSCRIBER_ENABLED:
            sub.stop()
            await task
```

### 实装 checklist

- [ ] 新建子包与空文件
- [ ] `_tick()` 返回 0 占位（PR-16 填）
- [ ] lifespan 集成 + 启动/退出日志
- [ ] 启动期不连 DB / 不创建 session pool 的 lazy 初始化（不动生产路径）
- [ ] `DISPATCH_SUBSCRIBER_ENABLED=0` 的情况下 **零副作用**（这是本 PR 最重要的不变量）

## 测试 Checklist

- [ ] 本地启动 Business（不设 env）→ 日志 `dispatch_subscriber disabled`，outbox 不被触碰
- [ ] 本地启动 Business + `DISPATCH_SUBSCRIBER_ENABLED=1` → 日志 `dispatch_subscriber enabled` + `starting worker_id=...`（但因 `_tick` 空转，不会有消费）
- [ ] 单测：`_tick()` 返回 0 → run 循环正常 sleep

## 可观测性 Checklist

- [ ] 启动 log：`dispatch_subscriber enabled|disabled`
- [ ] 运行 log（DEBUG）：`subscriber tick n=0 elapsed=XX ms`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P2-3（第一半）→ `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] 更新 `scripts/start.sh`：默认不设 `DISPATCH_SUBSCRIBER_ENABLED`（保持 off）

## 验收命令

```bash
# 默认 off
./scripts/start.sh
# 日志搜索
rg 'dispatch_subscriber' business.log
# 预期：`dispatch_subscriber disabled`

DISPATCH_SUBSCRIBER_ENABLED=1 ./scripts/start.sh
rg 'dispatch_subscriber' business.log
# 预期：`dispatch_subscriber enabled`
```

## 回滚

`git revert` — 骨架独立，无副作用。

## 备注

- 本 PR 不实现业务逻辑，纯挂载；分开是为了让 PR-16 的 review 聚焦"消费语义"而不是"生命周期"。
- lifespan 用 `@asynccontextmanager`（Cortex 已迁，Business 若还是 `@app.on_event` 本 PR 顺便迁）。
