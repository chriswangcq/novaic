# PR-15 Preflight Review — Dispatch Subscriber 骨架

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准**。补完 §A/§B/§C 3 处后直接 T1（不用再 review） |
| 亮点 | 正确定位部署在 Business lifespan；正确锚定 `msg:{id}` key 空间跟 inline 对齐 |

---

## §A（BLOCKER）Scope 漂移到 PR-16——preflight 有一半内容不属于 PR-15

回看 PR-15 ticket 原话：

> "本 PR 不实现业务逻辑，纯挂载；分开是为了让 PR-16 的 review 聚焦'消费语义'而不是'生命周期'"

PR-15 的唯一不变量是：**`DISPATCH_SUBSCRIBER_ENABLED=0` 时零副作用，`_tick()` 固定返回 0**。

你 preflight 的 §2（Claim SQL `UPDATE ... RETURNING`）、§3（指数退避、`attempts` 递增、死信流）、§4（双发并发语义细节）**全部属于 PR-16 scope**。PR-15 不需要这些——`_tick()` 根本不执行任何 DB 操作。

**返工要求**：

- §2 / §3 从 preflight 里**删掉**，或者挪到一个新章节"延后到 PR-16 preflight"，用 1-2 句话列出"将在 PR-16 决定的问题清单"，不要展开细节
- §4 保留（双发 key 对齐是正确的前置约束），但浓缩成 2-3 句话，不要重复证明

这不是挑刺——**scope 漂移的代价是 review 注意力被稀释，真正该决策的问题（§B）被埋没了**。你这次漏过的东西恰恰证明了这点。

### 元问题（下次注意）

preflight 的价值是"把本 PR 所有需要决策、但 ticket 没明说的技术选择找出来，给 senior 做裁决"。不是"把 phase 剩下的所有 PR 一次性设计完"。尺度感：**如果某个决策在 PR-15 里不需要写代码体现，就不该在 PR-15 preflight 里展开**。

## §B（BLOCKER）你漏掉了 PR-15 真正需要回答的问题：subscriber 怎么读 outbox？

ticket 的骨架代码：
```python
def __init__(self, db, assembler, *, ...):
    self.db = db
```

这个 `db=...` 是**占位符**，没指向任何具体对象。你 preflight 里通篇假设 "subscriber 直接读 outbox 表"，但**这和 PR-14 §1 你自己抓到的架构问题是同一种错误**：

| 问题 | PR-14 写路径 | PR-15 读路径 |
| --- | --- | --- |
| outbox 表在哪 | Entangled 的 `~/.novaic/data/entangled.db` | 同上 |
| Business 有没有 Entangled 的 db 句柄 | ❌ 没有 | ❌ 没有 |
| 跨进程通信机制 | HTTP（`/v1/entities/messages/append`） | **???**（你没回答） |

Business 和 Entangled 是两个独立进程（potentially 不同 host），Business 侧**无法**直接 open Entangled 的 SQLite 文件。所以 subscriber 读 outbox 行只有两条路：

1. **新增 Entangled HTTP 端点**：`POST /v1/outbox/claim`（原子 claim + fencing）、`POST /v1/outbox/mark_delivered`、`POST /v1/outbox/mark_failed`。Business subscriber 通过 `internal_async_client` 调用
2. **Subscriber 搬到 Entangled 里**：作为 Entangled 进程的内部协程；Business 只负责 lifespan 挂载点的假象

现在全仓 grep 确认 **Entangled 没有任何 `/v1/outbox/*` 端点**（只有 `entity_store.py` 里的 INSERT，没有 READ/UPDATE）。所以读路径的基础设施**还不存在**。

### PR-15 具体要做的决策

这个决策**属于 PR-16**，PR-15 骨架不该 commit 到具体方案。但 PR-15 的 `__init__` 签名会定型——如果这里写死 `db=...`，就隐式 commit 到"直接 SQL 访问"方案；等 PR-16 preflight 发现这走不通再改，就得改签名+改挂载+改测试。

**建议方案**：PR-15 的 `DispatchSubscriber.__init__` 只接受**真正骨架需要的东西**：

```python
def __init__(
    self,
    assembler: DispatchAssembler,
    *,
    poll_interval: float = 0.5,
    batch_size: int = 50,
    worker_id: Optional[str] = None,
):
    # db/outbox_reader 到 PR-16 再注入
    self.assembler = assembler
    ...
```

`_tick()` 返回 0 时根本不需要 `db`。把读 outbox 的抽象（无论是 `db` handle 还是 HTTP client）**延后到 PR-16 preflight 里决策并注入**。这样 PR-15 真正做到"零副作用 + 零架构承诺"。

preflight 里要明文写一节"§读路径抽象延后"，列出 PR-16 preflight 要回答的三个子问题：
1. HTTP 新端点（方案 A）vs Entangled 内部协程（方案 B）
2. claim/release/mark_delivered 的原子性保证（SQL RETURNING 还是 HTTP 事务）
3. Worker 多副本的 fencing 语义（多个 Business pod 都开 subscriber 时的抢占）

## §C（必改）事实性错误：`app.state.assembler` 不存在，Business 现在用 `get_assembler()` 模块单例

你 §执行计划 §3 写的：

> "app.state.assembler 和 app.state.db 都会在 lifespan 里被初始化，可以直接取用"

grep 验证：
```bash
$ rg 'app\.state\.assembler|get_assembler' novaic-business/
novaic-business/business/wake/assembler_factory.py:8:def get_assembler() -> DispatchAssembler:
novaic-business/business/message_actions.py:54:    assembler = get_assembler()
novaic-business/business/internal/subagent.py:407:    assembler = get_assembler()
```

**`app.state.assembler` 在 Business 中根本不存在**——PR-11 当时选了 `get_assembler()` 模块单例工厂模式（跟 Cortex / Runtime 对齐）。你自己在 PR-11 里写的代码。

### 修复

PR-15 的 lifespan 里复用相同模式：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    if SUBSCRIBER_ENABLED:
        from business.wake.assembler_factory import get_assembler
        from business.subscribers.dispatch_subscriber import DispatchSubscriber
        sub = DispatchSubscriber(assembler=get_assembler())
        task = asyncio.create_task(sub.run())
        app.state.subscriber = sub  # 存 handle 供关停
        logger.info("dispatch_subscriber enabled worker_id=%s", sub.worker_id)
    else:
        logger.info("dispatch_subscriber disabled (DISPATCH_SUBSCRIBER_ENABLED=0)")
    try:
        yield
    finally:
        if SUBSCRIBER_ENABLED:
            sub.stop()
            await task
```

preflight 把 "app.state.assembler" 改成 "get_assembler() 模块单例（沿用 PR-11 模式）"。

### 相关顺便确认

- Business 已经用 `@asynccontextmanager lifespan`（`main_business.py:100-101`），ticket 备注里"若还是 on_event 本 PR 顺便迁"的顾虑已经消除——preflight 可以 acknowledge 这点，省一个 side-task
- `DispatchSubscriber` 类在 `DISPATCH_SUBSCRIBER_ENABLED=0` 时**甚至不应 import**（惰性 import 放 `if` 分支里），保证"env=0 时连 class 都不加载"——这是"零副作用"不变量的最强证明

## §D（必做）测试设计你一字没提

ticket 测试 Checklist 3 条，你 preflight 没给任何 commitment：

- [ ] 本地启动 Business（不设 env）→ 日志 `dispatch_subscriber disabled`，outbox 不被触碰
- [ ] 本地启动 Business + `DISPATCH_SUBSCRIBER_ENABLED=1` → 日志 `dispatch_subscriber enabled` + `starting worker_id=...`
- [ ] 单测：`_tick()` 返回 0 → run 循环正常 sleep

### 必须回答的问题

1. **单测怎么写**：`run()` 是无限循环 `while not self._stop.is_set()`。测试要证明 `_tick()==0` 时会 sleep、`stop()` 后能退出。思路：
   ```python
   async def test_tick_zero_sleeps_then_stops():
       sub = DispatchSubscriber(assembler=mock_assembler, poll_interval=0.01)
       task = asyncio.create_task(sub.run())
       await asyncio.sleep(0.05)  # 让它 tick 几次
       sub.stop()
       await asyncio.wait_for(task, timeout=1.0)  # 必须能退出
   ```
   preflight 要明确给出测试骨架，不是"单测：_tick() 返回 0 → run 循环正常 sleep"这种笼统说法

2. **集成验证 stdout 怎么拿**：跟 PR-14 B.2 的 rework notes 一样——真的启动 Business（两种 env），grep 日志，把**真实 stdout** 贴进 T1 报告。不是"预期：`disabled`"就算验收

### "零副作用"怎么证

除了日志验证，还要一条硬证据：`DISPATCH_SUBSCRIBER_ENABLED=0` 时 Business 启动，**完全没有** `DispatchSubscriber` / `dispatch_subscriber` 相关 import 发生（用 `sys.modules` 检查）。或者用 `py-spy` / `pytest-instafail` 跑 startup 看 import tree。这条不 block，但写进 preflight 体现你考虑过。

## §E（信息性）Worker ID 的容器化陷阱

ticket 示例用 `socket.gethostname()`。Kubernetes 环境下，不同 pod 可能有**相同 hostname**（比如 sidecar 之类），`locked_by` 会冲突。

小 fix：`worker_id = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"`。

PR-15 骨架用不上（`_tick` 空转），但既然 ticket 要求初始化 `self.worker_id`，一步到位用安全格式，别留坑。preflight 里写一句"采用 hostname:pid:uuid 组合 worker_id"。

---

## 返工 Checklist

- [ ] §A 把 §2/§3/§4 浓缩或删除；§4 保留 3 句话（key 空间对齐结论即可）；新增"§读路径抽象延后到 PR-16"章节列 3 个子问题
- [ ] §B `DispatchSubscriber.__init__` 签名**不接 `db`**，只接 `assembler` + 轮询参数；`_tick` 返回 0 无 DB 依赖
- [ ] §C 修正 `app.state.assembler` → `get_assembler()` 模块单例；acknowledge lifespan 已经迁移
- [ ] §C 惰性 import（`if SUBSCRIBER_ENABLED: import ...`）保证 flag=0 时零 import
- [ ] §D 给出具体单测骨架（asyncio.Event + asyncio.create_task + wait_for 退出断言）
- [ ] §D 承诺集成验证走 PR-14 B.2 那种真实 stdout 方式，不打空勾
- [ ] §E `worker_id` 用 `hostname:pid:uuid[:8]` 格式

---

改完 preflight 直接上 T1，不用再来一轮 review。

### 给小弟的元反馈

PR-14 返工你做得很好，但 PR-15 preflight 出现了**另一个方向的偏差**——过度设计。"把 phase 剩下的 PR 也一次性想完"看似勤奋，实际上稀释了 PR-15 自己真正需要的决策（§B 的读路径抽象直接被你跳过了）。

**Preflight 尺度法则**：如果某个技术决定不会影响本 PR 的代码，它就不属于本 PR preflight。把它挪到后续 PR 的 preflight 再决策，这不是偷懒，是 scope discipline。PR-13 / PR-14 你在 scope 把控上做得好——这次退步了。下次 PR-16 preflight 是 claim/retry 的主场，到时候一次性说清即可。
