# PR-24  `LogContext` contextvar + 全服务 `scope_id` 日志绑定

| 字段 | 值 |
| --- | --- |
| **Phase** | 3 |
| **Milestone** | M3 |
| **承诺** | R4 |
| **Status** | `[ ]` |
| **Depends on** | PR-20 |
| **Blocks** | OBS-2 |
| **估时** | 1.5 d |
| **Owner** | __ |
| **PR 标题** | `feat(common+services): LogContext contextvar; bind scope_id at handler entry` |

## 目标

让 `rg "scope_id=<id>"` 跨所有后端服务日志能串起完整时间线。直接消解 hihi 事件"排查要人肉串四份日志"的问题。

## 范围

新建：
- `novaic-common/common/logging/__init__.py`
- `common/logging/context.py`

改造（每个服务的 handler 入口 + log formatter）：
- `novaic-business/`
- `novaic-agent-runtime/` (queue_service + task_queue handlers)
- `novaic-cortex/`
- `novaic-gateway/`

## 前置 Checklist

- [ ] PR-20 scope_id 可以在请求入口读到（payload / metadata）
- [ ] 确认各服务当前 log 方案（stdlib logging? structlog? 自定义?）→ 统一到 stdlib + filter

## 实施 Checklist

### 1. 公共 `LogContext`

```python
# common/logging/context.py
import contextvars, logging

_ctx: contextvars.ContextVar[dict] = contextvars.ContextVar("log_ctx", default={})

def bind(**kwargs):
    current = dict(_ctx.get())
    current.update({k: v for k, v in kwargs.items() if v is not None})
    _ctx.set(current)

def clear():
    _ctx.set({})

def current() -> dict:
    return _ctx.get()

class ContextFilter(logging.Filter):
    """Inject contextvar fields into every LogRecord."""
    def filter(self, record):
        for k, v in _ctx.get().items():
            setattr(record, k, v)
        return True

def install(logger: logging.Logger):
    f = ContextFilter()
    logger.addFilter(f)
    for h in logger.handlers:
        h.addFilter(f)

DEFAULT_FIELDS = ["scope_id", "agent_id", "user_id", "caller"]

def default_format() -> str:
    extras = " ".join([f"{k}=%({k})s" for k in DEFAULT_FIELDS])
    return f"%(asctime)s %(levelname)s %(name)s {extras} - %(message)s"
```

### 2. 每个服务的 bootstrap

- [ ] 启动期：`logging.basicConfig(format=default_format(), ...)` + `install(root_logger)`
- [ ] 为 `%(scope_id)s` 等在记录未绑定时给默认：用 `logging.LoggerAdapter` 或 `Filter` 补 `""` 默认值（避免 KeyError）
- [ ] Formatter 的缺省 "scope_id=" 输出为空串，不污染

### 3. Handler 入口 bind

对每个能进入 agent 流的入口点，第一行 bind 语义：

- [ ] Queue Service `dispatch` handler: `bind(agent_id=..., user_id=..., caller=req.headers.get("X-Internal-Service"))`
- [ ] Queue Service session 相关：若已知 scope_id，`bind(scope_id=...)`
- [ ] Cortex session.init / skill.* handlers: `bind(scope_id=scope_id, agent_id=agent_id, user_id=user_id)`
- [ ] Business subagent_send / spawn_subagent / bulk-transition handlers: `bind(agent_id=..., caller=...)`
- [ ] Task worker / saga worker 消费任务时：`bind(scope_id=task.scope_id, ...)`
- [ ] Subscriber `_deliver_one`：`bind(agent_id=..., message_ids=...)` 以及成功后 `bind(scope_id=result.scope_id)`
- [ ] runtime `handle_session_init`: `bind(scope_id=..., agent_id=...)`

每个 handler 返回前 `clear()`（ContextVar 是请求隔离的，但显式 clear 更保险，特别是 worker thread 复用时）

### 4. 分布式透传（可选）

- [ ] 跨服务 HTTP 调用自动带 `X-Scope-Id` header（`internal_client` 升级：从 contextvar 读 scope_id 自动注入）
- [ ] 目标服务 middleware 读 `X-Scope-Id` → bind；否则保留已有值

## 测试 Checklist

- [ ] 单测：bind + log → record 含 scope_id
- [ ] 单测：多个 Task（contextvar 隔离）互不污染
- [ ] 集成：发消息 → 取一个 scope_id → `rg "scope_id=<id>" business.log queue-service.log cortex.log runtime.log` 在每份日志都能命中

## 可观测性 Checklist

- [ ] OBS-2 达成：`rg scope_id=<id>` 跨服务可串
- [ ] 留 runbook 示例

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P3-5 → `[x]`
- [ ] OBS-2 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] 新建 `docs/runbooks/troubleshooting.md` 或扩展已有一节："按 scope_id 查问题的 SOP"

## 验收命令

```bash
# 发消息触发一个 scope
# 取 scope_id
SID=$(sqlite3 ~/.novaic/data/entangled.db "SELECT claimed_by_scope FROM chat_messages ORDER BY created_at DESC LIMIT 1;")
# 跨日志聚合
rg "scope_id=$SID" business.log queue-service.log cortex.log runtime.log | sort -k1,2
# 预期：每份日志都有 ≥ 1 行
```

## 回滚

`git revert` —— 回到无 scope_id 的日志，排查回到人肉模式。

## 备注

- 这个 PR 是 Phase 3 的"核心工具"，上线前请在本地完整走一次 SOP 排查 demo，写在 runbook 里。
- Python 的 `logging` + `Filter` 在多 worker / asyncio 下行为要测；建议先在一个服务试点，再推广。
