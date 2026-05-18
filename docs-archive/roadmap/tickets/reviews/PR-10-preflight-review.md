# PR-10 Preflight Review（DispatchAssembler）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准**（补完 §B 六条后直接开 T1，不用再 review 一轮） |
| Target preflight | `docs/roadmap/tickets/reviews/PR-10-preflight-antigravity.md` |

---

## §A  方向正确的部分

- 入口收敛定位准确：`common/wake/assembler.py` 为唯一单点
- 6 条异常路径测试覆盖完整（`bad_argument / no_owner / queue_400 / queue_5xx / network / assemble 成功`）
- 合约测试 `test_assembler_queue_schema.py` 的思路对 —— 把 Assembler 的 `to_queue_payload()` 喂给 Queue Service 的 Pydantic `DispatchRequest.model_validate`
- §5 "Assembler 不含 retry" 纪律明确
- 提前开 PR-10 preflight、利用 24h 观察期，时间管理得当

## §B  必须补进 preflight 的 6 条

### B.1  §6 事实错误 —— `get_resolver()` **没有**"退回为 sync"

你写的："PR-08 验收中明确：`AgentOwnershipResolver.get_resolver()` 被退回为了 sync 方法（避免绑定 event loop）。"

事实：PR-08 t1-rework review §B 里我明确说"**不让你现在返工**"，只在 `technical-debt.md:38` 登记了 TD。`get_resolver()` 现在仍是 `async def` + 模块级 `asyncio.Lock()`，未修复。

**两个决定二选一，preflight §6 必须写清**：

- **选项 1（推荐）**：PR-10 顺手把 `get_resolver()` 改回 sync 工厂（删 `async` + 删锁，trivial 改动），同时从 `technical-debt.md` 划掉该 TD。理由：PR-10 是第一个消费者，自然修复点。
- 选项 2：PR-10 **完全不使用** `get_resolver()`，调用方（PR-11/12/13）自己构造 resolver 实例传进 Assembler，TD 继续挂着。

我倾向 **选项 1**。代价：2 行代码 + 1 行 TD 删除，无新测试。收益：TD 清一条。

### B.2  Metrics `[-]` 连续第 2 次延后 —— 必须开 backlog 票兜底

PR-06 metric counter 已 `[-]`、本次 PR-10 的 `dispatch_total / dispatch_latency_seconds` 又 `[-]`。再延后下去 metrics 永远不落地。

**必做**：在 `docs/roadmap/tickets/` 下**新建**一张 `PR-XX-metrics-prometheus-integration.md`（或者如果就挂在 PR-19 下更合适、就在 PR-19 ticket 里显式写入 "接管以下 `[-]` metric"），**显式列出所有被 `[-]` 的 metric**，至少：

- `internal_requests_total{caller, target, status}` counter (PR-06)
- `ownership_resolver_total{result=hit|miss|error}` counter + `ownership_resolver_latency_seconds` histogram (PR-08)
- `dispatch_total{trigger_type, result}` counter + `dispatch_latency_seconds{trigger_type}` histogram (PR-10)
- `agent_owner_lookup_total{result=hit|miss}` counter (PR-07)

preflight §4 把这条"backlog 票地址"写明。不要留"延后到后续 cleanup"这种开放式措辞。

### B.3  `DispatchRequest` 命名碰撞 —— 必须用 alias

`common/wake/assembler.py` 定义 `@dataclass DispatchRequest`，而 `queue_service/routes.py` 已有 Pydantic `DispatchRequest`（现有）。合约测试 `test_assembler_queue_schema.py` 里必须：

```python
from common.wake.assembler import DispatchRequest as AssemblerDispatchRequest
from queue_service.routes import DispatchRequest as QueueDispatchRequest
```

preflight §2 或 §3 加一条注释："两端 `DispatchRequest` 同名不同物 —— Assembler 端是 dataclass，Queue 端是 Pydantic。合约测试用 alias 区分。"

### B.4  Queue `/dispatch` 端点归属澄清

你的 file:line 表**没列 Queue Service 端点**，让人以为 PR-10 不依赖 Queue 侧。事实上：

- **端点已存在**：`novaic-agent-runtime/queue_service/routes.py:510` `@router.post("/dispatch")`，最终路径 `/api/queue/dispatch`（main.py:252 有 alias map）
- **本 PR 不改 Queue 侧**（§5 也说了"不动调用方"）

在 file:line 表加一行 **只读引用**（类似 PR-08 的"未来调用方"那种 "本 PR 不改动，仅登记合约"）：

| 文件 | 动作 |
| --- | --- |
| `novaic-agent-runtime/queue_service/routes.py:510` | 本 PR **不改动**，仅作合约测试目标（`DispatchRequest` Pydantic schema） |

### B.5  Resolver 注入方式 —— 用 DI，不要内部 `get_resolver()`

§6 说"直接实例化或传入 resolver 实例"——模糊。明确写：

> `DispatchAssembler.__init__(resolver: AgentOwnershipResolver, queue_base_url: str, *, service_name: str = "assembler")` —— resolver **强制由调用方注入**，Assembler 内部**不**调用 `get_resolver()`。测试时 mock resolver 直接传入即可。

这和 B.1 的选项 1 一起做最干净。

### B.6  `DispatchError` 数据结构要和 ticket 对齐

ticket §143-145 明确了：

```python
@dataclass
class DispatchError(Exception):
    msg: str
    kind: Literal["bad_argument","no_owner","queue_400","queue_5xx","network"]
    status: int | None = None
```

当前 `novaic-common/common/wake/errors.py:3-8` 是 `__init__(msg="", *, kind=None, status=None)`，**不是 dataclass 形式，kind 也不是 Literal 约束**。

preflight §2 第 2 行 "扩展 DispatchError 新增对 kind 的支持" 太泛。明确写清楚：

> 将 `DispatchError` 从 plain class **重构为 `@dataclass`**，`kind` 字段类型收紧为 `Literal["bad_argument","no_owner","queue_400","queue_5xx","network"]`。**验证 PR-08 的 `raise DispatchError(kind="network", status=...)` 在 dataclass 形式下仍然成立**（dataclass 的 init 签名是位置+关键字混合，可能需要 `kw_only=True` 或保持 `__init__` 兼容）。

这条不做，PR-08 的测试会回归。

## §C  不阻塞的提醒

- **24h 观察期 gate**：PR-10 合并前必须确认 PR-09 生产上跑满 24h 无异常。写进 preflight §5。
- **E2E 合约测试的 PYTHONPATH**：跨包 import `queue_service.routes.DispatchRequest` 时需要同时加 `novaic-agent-runtime` 到 `PYTHONPATH`。在合约测试文件顶部写清运行命令（或加 conftest.py），避免下一个人跑单测时一脸懵。
- **Scope lock 跨进程校验**：Queue `/dispatch` 内部会拿 scope lock（PR-06 顺带的 observability）。Assembler 端是否需要关心？—— 不需要，Assembler 只发送 HTTP；状态同步由 Queue 处理。在 preflight §5 补一句以免被误解。

## §D  开 T1 前的最小清单

- [ ] 补完 §B 六条（改 preflight，不改代码）
- [ ] 确认 PR-09 已跑满 24h 观察期
- [ ] 如选 §B.1 选项 1：T1 时同步把 `get_resolver()` 改回 sync + 删 `technical-debt.md` 对应行
- [ ] Declare done 前反向 `rg` 自检每个 `[x]`（上次 PR-09 的假勾教训）
