# PR-08  `AgentOwnershipResolver` 实现（带 TTL 缓存）

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R3 |
| **Status** | `[ ]` |
| **Depends on** | PR-01, PR-02, PR-05, PR-07 |
| **Blocks** | PR-10 |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(common): AgentOwnershipResolver with TTL cache` |

## 目标

替换掉所有上游代码里 "自己拼 user_id" 的行为，唯一进程内 resolver。Cortex 的 tenant 约束从此止步于 Assembler，不再外泄到上游 HTTP 契约。

## 范围

- `novaic-common/common/agents/ownership.py`（PR-02 已放占位，这里实装）

## 前置 Checklist

- [ ] PR-07 合并 + Business 已上线端点
- [ ] PR-05 合并 + `internal_client` 可用

## 实施 Checklist

### 类签名

```python
class AgentOwnershipResolver:
    def __init__(
        self,
        business_base_url: str,
        *,
        ttl_seconds: float = 300.0,
        service_name: str = "resolver",
    ):
        self._client = internal_client(service_name=service_name, base_url=business_base_url)
        self._cache: dict[str, tuple[str, float]] = {}  # agent_id -> (user_id, expires_at)
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()

    async def resolve(self, agent_id: str) -> str:
        """Returns user_id; raises AgentNotOwnedError if not found or no owner."""

    async def invalidate(self, agent_id: str) -> None:
        """Manual cache drop (optional)."""

    def _now(self) -> float:
        return time.monotonic()
```

### 必做

- [ ] 缓存命中 + 未过期 → 直接返回
- [ ] 过期/未命中 → 调 `GET /internal/agents/{id}/owner`
  - 200 → 存缓存，返回
  - 404 → 抛 `AgentNotOwnedError(agent_id=...)`（不缓存负例，避免竞态：agent 刚创建）
  - 网络错误 / 5xx → 抛 `DispatchError(kind="network", ...)`（不伪装成 404）
- [ ] 并发保护：同一 `agent_id` 并发 resolve 只发一次 HTTP（用 `asyncio.Lock` 或 per-key future）
- [ ] 无静默降级：**任何**失败都 raise

### 不做

- [ ] 不做多级缓存（进程内 dict 够）
- [ ] 不做 prefetch / batch（需要时 PR-30+ 再补）
- [ ] 不做持久化（进程重启缓存清空，符合 TTL 语义）

### 全局注入点

- [ ] 提供一个模块级 `get_resolver()` 工厂（首次调用 lazy init，从 env 读 `BUSINESS_INTERNAL_URL`）
- [ ] 或让 `DispatchAssembler` 构造时接收 resolver 实例（PR-10 决定）

## 测试 Checklist

- [ ] `tests/test_ownership.py`:
  - [ ] 命中 → 直接返回，0 次 HTTP
  - [ ] 首次 → 1 次 HTTP，结果进缓存
  - [ ] TTL 过期 → 再发一次 HTTP
  - [ ] 404 → `AgentNotOwnedError`
  - [ ] 网络错误 → `DispatchError(kind="network")`
  - [ ] 并发 resolve 同一 id → 只一次 HTTP（需 mock 可计数）

## 可观测性 Checklist

- [ ] metric `ownership_resolver_total{result=hit|miss|error}` counter
- [ ] metric `ownership_resolver_latency_seconds` histogram（miss 路径）
- [ ] log（DEBUG 级）：`resolver hit agent_id=... user_id=... from=cache|http`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P1-3（第二半）→ `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] 在 [architecture/authentication.md](../../architecture/authentication.md) 或新文档说明 "Cortex tenant 约束止于 Assembler"

## 验收命令

```bash
python -c "
import asyncio, os
from common.agents.ownership import AgentOwnershipResolver, AgentNotOwnedError
r = AgentOwnershipResolver('http://localhost:8200')
print(asyncio.run(r.resolve('<some-agent-id>')))
"
```

```bash
# 性能验证：第二次应瞬时返回
python -c "
import asyncio
from common.agents.ownership import AgentOwnershipResolver
r = AgentOwnershipResolver('http://localhost:8200')
async def go():
    await r.resolve('<id>')
    import time; t=time.perf_counter(); await r.resolve('<id>')
    print('cached lookup:', (time.perf_counter()-t)*1000, 'ms')
asyncio.run(go())
"
# 预期 < 1ms
```

## 回滚

`git revert` — 若 Assembler (PR-10) 依赖已合并，需要一起 revert。

## 备注

- TTL 默认 5 min，可后续暴露为配置。Agent owner 本来就不会变，5 min 非常宽松。
- "缓存 404" 的诱惑：不要做，避免 "新建 agent 但缓存还是 404" 的诡异场景。
