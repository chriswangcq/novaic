# PR-10  `DispatchAssembler` 本体 + 合约测试 ⭐ 关键 PR

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R2 + R3 |
| **Status** | `[x]` |
| **Depends on** | PR-05, PR-08, PR-09 |
| **Blocks** | PR-11, PR-12, PR-13, PR-15 |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `feat(common): DispatchAssembler — single entry for all wake dispatches` |

## 目标

把"`agent_id + trigger → Queue /dispatch 请求体`"这件事**收敛到唯一函数**。上游所有触发点经此组装；Queue Service 的 `/dispatch` 合约变化只影响这一处。

## 范围

- `novaic-common/common/wake/assembler.py`（PR-01 占位）
- `novaic-common/common/wake/errors.py`（完善 `DispatchError.kind`）
- `tests/contract/test_assembler_queue_schema.py`（合约测试）

## 前置 Checklist

- [x] PR-05/08/09 全部合并并可用
- [x] Queue Service `DispatchRequest` Pydantic model 可以 import（用于合约测试）

## 实施 Checklist

### Data classes

```python
# common/wake/assembler.py
from dataclasses import dataclass, field
from typing import Literal
from common.wake.trigger_types import TriggerType
from common.wake.errors import DispatchError, AgentNotOwnedError
from common.agents.ownership import AgentOwnershipResolver
from common.http.clients import internal_client

@dataclass(frozen=True)
class DispatchRequest:
    agent_id: str
    user_id: str
    subagent_id: str
    trigger_type: TriggerType
    message_ids: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)

    def to_queue_payload(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "subagent_id": self.subagent_id,
            "trigger_type": self.trigger_type.value,
            "metadata": {
                **self.metadata,
                "message_ids": list(self.message_ids),
            },
        }

@dataclass(frozen=True)
class DispatchResult:
    session_id: str
    scope_id: str | None
    buffered: bool          # True = same-agent active session, message queued
    raw: dict
```

### Core class

```python
class DispatchAssembler:
    def __init__(
        self,
        resolver: AgentOwnershipResolver,
        queue_base_url: str,
        *,
        service_name: str = "assembler",
    ):
        self._resolver = resolver
        self._client = internal_client(service_name=service_name, base_url=queue_base_url)

    async def assemble(
        self,
        trigger_source: TriggerType,
        agent_id: str,
        *,
        subagent_id: str | None = None,
        message_ids: list[str] | None = None,
        metadata: dict | None = None,
    ) -> DispatchRequest:
        if not isinstance(trigger_source, TriggerType):
            raise DispatchError("trigger_source must be TriggerType", kind="bad_argument")
        try:
            user_id = await self._resolver.resolve(agent_id)
        except AgentNotOwnedError as e:
            raise DispatchError(f"no owner for {agent_id}", kind="no_owner") from e
        sub_id = subagent_id or f"main-{agent_id[:8]}"
        return DispatchRequest(
            agent_id=agent_id,
            user_id=user_id,
            subagent_id=sub_id,
            trigger_type=trigger_source,
            message_ids=tuple(message_ids or ()),
            metadata=metadata or {},
        )

    async def dispatch(self, req: DispatchRequest) -> DispatchResult:
        try:
            resp = await self._client.post("/api/queue/dispatch", json=req.to_queue_payload())
        except httpx.RequestError as e:
            raise DispatchError(str(e), kind="network") from e
        if resp.status_code >= 500:
            raise DispatchError(resp.text, kind="queue_5xx", status=resp.status_code)
        if resp.status_code >= 400:
            raise DispatchError(resp.text, kind="queue_400", status=resp.status_code)
        body = resp.json()
        return DispatchResult(
            session_id=body["session_id"],
            scope_id=body.get("scope_id"),
            buffered=bool(body.get("buffered", False)),
            raw=body,
        )

    async def assemble_and_dispatch(self, trigger_source, agent_id, **kw) -> DispatchResult:
        req = await self.assemble(trigger_source, agent_id, **kw)
        return await self.dispatch(req)
```

### Error class

```python
# errors.py
from dataclasses import dataclass

@dataclass
class DispatchError(Exception):
    msg: str
    kind: Literal["bad_argument","no_owner","queue_400","queue_5xx","network"]
    status: int | None = None

    def __str__(self): return f"DispatchError(kind={self.kind}, status={self.status}): {self.msg}"
```

### 实装 checklist

- [x] `assemble` 不做 HTTP（只组装）；`dispatch` 做 HTTP
- [x] 所有失败路径 raise `DispatchError`，带明确 `kind`
- [x] `metadata.message_ids` 必含（Queue Service 会透传到 scope）
- [x] `subagent_id` 默认 `main-<agent_id[:8]>`（与现有惯例一致）
- [x] log：`dispatch agent=... trigger=... user=... sub=... messages=<n> result=ok|<kind>`

## 测试 Checklist

### 单测

- [x] `tests/test_assembler.py`:
  - [x] `assemble` 正常路径 → DispatchRequest 字段齐全
  - [x] `assemble` 非法 trigger_source (str) → `DispatchError(kind="bad_argument")`
  - [x] resolver raise `AgentNotOwnedError` → `DispatchError(kind="no_owner")`
  - [x] `dispatch` 200 → DispatchResult
  - [x] `dispatch` 400 → `DispatchError(kind="queue_400")`
  - [x] `dispatch` 500 → `DispatchError(kind="queue_5xx")`
  - [x] `dispatch` httpx 错误 → `DispatchError(kind="network")`
  - [x] `subagent_id` 显式传入覆盖默认

### 合约测试

- [x] `tests/contract/test_assembler_queue_schema.py`:
  - [x] 构造 DispatchRequest → `to_queue_payload()` → 用 Queue Service 的 `DispatchRequest` Pydantic model validate → 必通过
  - [x] 覆盖每个 TriggerType

## 可观测性 Checklist

- [x] metric `dispatch_total{trigger_type, result=ok|no_owner|queue_400|queue_5xx|network}` counter — 落地于 PR-32，五个 raise 点对称打点
- [x] metric `dispatch_latency_seconds{trigger_type}` histogram — 落地于 PR-32，`dispatch_sync` POST 外围包 `metric_timer`
- [x] log 结构化：`event=dispatch trigger=... agent=... user=... messages=... result=...`

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) P1-5 → `[x]`
- [x] 本工单 Status → `[x]`
- [/] 在 [cortex/internal-api-schemas.md](../../cortex/internal-api-schemas.md) 或新建 `docs/common/dispatch-assembler.md` 给 Assembler 画一张调用流程图 (暂缓，后续统一)
- [x] 在 [message-wake-principles.md](../../architecture/message-wake-principles.md) §R2 引用本 PR 代码

## 验收命令

```bash
cd novaic-common && python -m pytest tests/test_assembler.py tests/contract/ -v
```

```python
# REPL 手调
import asyncio
from common.agents.ownership import AgentOwnershipResolver
from common.wake.assembler import DispatchAssembler
from common.wake.trigger_types import TriggerType

async def go():
    r = AgentOwnershipResolver("http://localhost:8200")
    a = DispatchAssembler(r, "http://localhost:7000")
    res = await a.assemble_and_dispatch(
        TriggerType.USER_MESSAGE,
        "<agent_id>",
        message_ids=["<msg_id>"],
    )
    print(res)
asyncio.run(go())
```

## 回滚

- 本 PR 独立，无现有调用方（PR-11/12/13 之后才有）→ revert 不影响运行。

## 备注

- **这是全计划最关键的 PR**；务必完备的单测 + 合约测试。
- 任何 `to_queue_payload` 格式变化必须同步 Queue Service 并走一次 PR-10 的合约测试。
- 不要把 retry / backoff 放在 Assembler 里 —— 那是 subscriber (PR-16) 的责任。Assembler 只"组装 + 发一次"。
