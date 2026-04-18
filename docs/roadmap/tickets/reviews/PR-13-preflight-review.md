# PR-13 Preflight Review（Scheduler → DispatchAssembler）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准** — 补完 §A 的 blocker + §B/§C/§D 事实错误后可直接 T1 |
| 亮点 | 抓到了 `idempotency_key` 缺失，这是 PR-10 遗留的合约漏洞 |

---

## §A（BLOCKER）`idempotency_key` 是 PR-10 Assembler 遗留漏洞，必须带修

### 事实确认

Queue 端 `routes.py:483` 的 `DispatchRequest`：
```python
idempotency_key: Optional[str] = None
```
PR-10 Assembler 的 `DispatchRequest`（`common/wake/assembler.py:15`）：
```python
@dataclass(frozen=True)
class DispatchRequest:
    agent_id: str
    user_id: str
    subagent_id: str
    trigger_type: TriggerType
    message_ids: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)
    # ❌ 没有 idempotency_key
```

PR-10 的 `test_assembler_queue_schema_contract` **没抓到**这个缺口，因为 Queue 侧字段是 `Optional`，Pydantic `model_validate({...})` 不传也通过。这是**契约测试的假阳性**——只检查了"我送的字段 Queue 能收"，没检查"Queue 能收的字段我都能送"。

### 返工要求

1. **把改动拆成独立 commit**，attribution 明确：
   - commit 1（子模块 novaic-common）：`fix(wake): expose idempotency_key on DispatchRequest (PR-10 retroactive fix)`
     - `DispatchRequest` 加 `idempotency_key: Optional[str] = None`
     - `to_queue_payload()` 透传
     - `DispatchAssembler.assemble(...)` / `assemble_and_dispatch(...)` 加 `idempotency_key` kwarg
   - commit 2（子模块 novaic-common）：`test(wake): contract test covers idempotency_key both present/absent`
     - 改 `test_assembler_queue_schema.py`：对每个 TriggerType **加 2 组 case**（`idempotency_key="k-1"` 和 `idempotency_key=None`）
     - 加一条 `test_to_queue_payload_includes_idempotency_key_when_set` unit test，断言 `payload["idempotency_key"] == "k-1"`
   - commit 3（子模块 novaic-common）：本 PR-13 的 Assembler 相关改动（如果有）
   - commit 4（子模块 runtime）：`feat(runtime): scheduler routes through DispatchAssembler (PR-13)`
   - commit 5（主仓）：`chore: bump novaic-common + novaic-agent-runtime for PR-13`
   - commit 6（主仓）：docs + CI

2. **契约测试必须先红再绿**：先跑新测试证明当前 Assembler 不透传 `idempotency_key`（FAIL），再改 Assembler，再跑绿。这跟你 PR-10 C.1/C.2 的 Red-Green 纪律一样。

3. **更新 PR-10 T1 review 文档**或 `technical-debt.md` 加一条总结：`test_assembler_queue_schema_contract` 原版只检查单向，现已补强双向。

---

## §B（事实错误）§8 CI allowlist 的改法是错的

你写："删除 `ALLOWLIST` 里的 `scheduler_worker_sync.py` 相关行"。

**实际**：`scripts/ci/lint_dispatch.sh` 里**没有** `scheduler_worker_sync.py`，因为这个文件压根不含字符串 `/api/queue/dispatch`——它走 `SagaClient.dispatch()` 封装，HTTP 字符串在 `task_queue/client.py` 里。

当前 allowlist 长这样：
```
'novaic-common/common/wake/assembler.py'
'novaic-agent-runtime/queue_service/main.py'  # 端点定义
# TRANSITIONAL — remove after PR-12/PR-13:
'novaic-agent-runtime/task_queue/client.py'
'tests/'
```

正确动作：
- **不要在 PR-13 里动 allowlist**。`task_queue/client.py` 标注是"PR-12/PR-13 都完成后才能移除"——PR-12 HealthWorker 可能还在用 `SagaClient.dispatch`。
- 在 PR-13 ticket 的"文档 Checklist"里把"PR-03 allowlist 移除 `scheduler_worker_sync.py`"这条**改成** `[-] 本 PR 不适用（scheduler 无直接 HTTP 字符串）`。
- PR-12 preflight 里再确认一次：PR-12 完成后才能删 `task_queue/client.py` 的 allowlist 条目，同时可能需要从 `SagaClient` 删 `dispatch()` 方法（如果只有 Scheduler + HealthWorker 两个使用者）。

---

## §C（必做）async 化覆盖不全：还有一处 `worker.run()` 和 `time.sleep`

你在 §4 说 `start_worker` 用 `asyncio.run(worker.run())`。但源码有**两个入口**：

- `scheduler_worker_sync.py:239` `start_worker()` 里的 `worker.run()` ✅ 你记得了
- `scheduler_worker_sync.py:285` `if __name__ == "__main__"` 最末 `worker.run()` ❌ preflight 没提

两处都必须改成 `asyncio.run(worker.run())`。

另外 `time.sleep` 有两处：
- `:95` 正常 tick 间歇 ✅ 你提了
- `:103` `except Exception` 后的 sleep ❌ preflight 没提

两处都要 `await asyncio.sleep`。T1 实施时 `rg 'time\.sleep|worker\.run\(\)' scheduler_worker_sync.py` 自查。

---

## §D（必做）死代码 + `DispatchResult` 语义缺口

### D.1 `saga_client` 实例变成死代码
迁移后 `SagaClient` 只在 `.close()` 里还被提及（`:79` 构造、`:107` 关闭）。应当：
- 删 `self.saga_client = SagaClient(...)` 构造
- 删 `from task_queue.client import ... SagaClient` import（只留 `BusinessClient`，它仍用于 `get_due_for_wake()`）
- 删 `finally` 里的 `self.saga_client.close()`

preflight §1 要把这个 cleanup 列到修改范围里。

### D.2 `DispatchResult` 没有 `action` 字段，但 Scheduler 要保留 3 个计数器

现有 metrics 区分三种状态：
```python
self.metrics.dispatch_started   # action == "saga_started"
self.metrics.dispatch_buffered  # action == "buffered"
self.metrics.dispatch_deduped   # action == "deduped"
```

PR-10 `DispatchResult` 是：
```python
@dataclass(frozen=True)
class DispatchResult:
    session_id: str
    scope_id: str | None
    buffered: bool
    raw: dict
```

只有 `buffered` 一个 bool，区分不了 `saga_started` vs `deduped`。

**两个方案**（preflight 钉死一个）：

- **方案 A（推荐）**：临时用 `result.raw.get("action")` 映射三态，**同时** 在 `technical-debt.md` 加 TD：`DispatchResult` 没有显式 `action` 枚举，Scheduler 靠 `raw.get("action")` 做分支，后续（PR-19/20 cleanup）应在 DispatchResult 引入明确 `ActionKind` enum。
- **方案 B**：本 PR 一起给 `DispatchResult` 加 `action: Literal["saga_started", "buffered", "deduped"]`，contract test 同步补。scope 更大但更彻底。

选 **方案 A**，TD 写清楚。方案 B 留给后续统一治理。

---

## §E（信息性，不 block）

### E.1 结构化日志用 `logger` 不要用 `print`
`_log` 当前是 `print(...)`。你在 §6 列的新格式 `event=scheduled_wake agent=... due_at=... result=ok|...` 建议用 `logger.info/error`，走标准 log 管道，别继续混进 `print`。原有 `_log` 调用可以不动（避免 diff 爆炸），新增的 `event=...` 日志独立用 logger。

### E.2 `user_id` 重复解析
Scheduler 已经从 `get_due_for_wake()` 拿到 `user_id`，但 `Assembler.assemble(agent_id)` 内部又会调 `resolver.resolve(agent_id)` 去 Business 查一次 owner。

不是 bug——TTL cache 会兜底。提一下让你心里有数。如果后续 scheduler 规模起来发现 resolver 成本高，可以考虑给 Assembler 加一个"bypass resolve 用传入的 user_id"的可选参数。当前不做。

### E.3 文件名 "scheduler_worker_**sync**.py" 在 async 化后是误导
不改名（避免 diff 炸），但在 TD 里记一笔，PR-18 cleanup 时统一重命名为 `scheduler_worker.py`。

---

## 返工 Checklist（preflight 修订要点）

- [ ] §A Assembler `idempotency_key` 字段 + 双向契约测试；在 preflight §3 说明提交顺序与 attribution
- [ ] §B §8 CI allowlist 表述改正，说明"本 PR 不适用"
- [ ] §C `__main__` 入口 + `except` 分支的 `time.sleep` 也要覆盖
- [ ] §D.1 `saga_client` 死代码 cleanup 写进 §1 范围
- [ ] §D.2 `action` 三态映射选方案 A + 登记 TD
- [ ] §E.1 新结构化日志用 `logger` 说明清楚
- [ ] §E.2 resolver 重复查询现象记一下
- [ ] §E.3 文件名误导登 TD

修完 preflight 直接 T1，不用再 review 一轮。
