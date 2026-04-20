# PR-24  `LogContext` contextvar + 全服务 `scope_id` 日志绑定

| 字段 | 值 |
| --- | --- |
| **Phase** | 3 |
| **Milestone** | M3 |
| **承诺** | R4 |
| **Status** | `[x]` (2026-04-15) |
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

## 实施总结（2026-04-15）

### 1. 公共包改造（`novaic-common`）

* `common/log_context.py` — 原先只有 `caller_var` 一个字段，现在扩成完整
  LogContext：
  - `bind(**fields)` / `clear()` / `current()` / `scope(**fields)` 上下文管理器。
  - `ContextFilter`：把 `_ctx.get()` 注入每条 `LogRecord` 的属性，
    让格式串 `%(scope_id)s` 对未 bind 的记录不 KeyError（输出空串）。
  - `install(logger=None)`：往 root logger 和它现有的 handler 上挂
    ContextFilter，幂等。
  - `default_format()`：统一格式 `"%(asctime)s [%(levelname)s] %(name)s
    scope_id=%(scope_id)s agent_id=%(agent_id)s user_id=%(user_id)s
    caller=%(caller)s - %(message)s"`。
  - `install_service_logging(service_name, ...)`：一次性 bootstrap，
    替代老的 `logging.basicConfig(...)`。
  - `caller_var` 保留做前向兼容，bind() 会顺手同步它。

* `common/middlewares/caller_logging.py` — `CallerLoggingMiddleware`
  现在除了读 `X-Internal-Service`，同时读 `X-Scope-Id` / `X-Agent-Id` /
  `X-User-Id` 并 bind 到 `_ctx`；handler 结束时在 `finally` 里 reset
  token，worker thread 复用时不会污染下一次请求。

* `common/http/clients.py` — `internal_sync_client` / `internal_async_client`
  都挂了 `event_hooks={"request": [_inject_logctx_headers(_async)]}`，
  在发请求之前从 `_ctx.get()` 读 scope/agent/user 并塞进 Header
  （caller 显式 setdefault 的优先）。至此跨服务 trace 不需要任何调用点
  手动传递。

* 新增 `tests/test_log_context.py` 16 个单测，覆盖：
  bind/current 往返、None 不覆盖、类型强转、caller_var 同步、
  `scope()` 退出还原、异常时也还原、clear、asyncio 并发隔离、
  ContextFilter 注入 LogRecord、install 幂等、middleware 读 4 字段、
  middleware 处理完 clear、缺 Header 时字段为空、HTTP 客户端注入
  Header、显式 Header 不被覆盖、未 bind 时不注入空 Header。

### 2. 服务 bootstraps（5 个服务）

全部把 `logging.basicConfig(...)` 换成：

```python
from common.log_context import install_service_logging
install_service_logging("<service>", handlers=[...])
```

落地到：
- `novaic-business/main_business.py`
- `novaic-gateway/main_gateway.py`
- `novaic-cortex/novaic_cortex/main_cortex.py`
- `novaic-agent-runtime/queue_service/main.py`
- `novaic-agent-runtime/main_novaic.py`（covers task/saga/health/scheduler）
- `novaic-device/main_device.py`

所有服务已挂 `install_caller_middleware`（历史 PR-06），本 PR
扩展 middleware 的字段数，不需要再改注册点。

### 3. 源头 bind（origination）

- **Runtime `handle_session_init`**（scope_id 唯一的出生地点）：
  校验完 payload 立刻 `bind(scope_id, agent_id, user_id)`。之后所有
  调 Cortex / Business / Queue 的 `httpx.Client` / `AsyncClient`
  自动带 X-Scope-Id 过去。
- **Subscriber `_deliver_one`**：进入时用 `scope(agent_id=...)` 上下文
  管理器包住整个 delivery（异常也能还原）；拿到 `result.scope_id` 后
  再 bind scope_id，让 transition_claimed / append_input 的日志都挂上。

### 4. Runbook

`docs/runbooks/troubleshooting.md` 新增「跨服务按 scope_id 查问题」一节
（SOP + rg 命令 + 常见信号）。

### 未覆盖 / 后续

- Task / Saga Worker 的「从队列领到任务 → bind」——当前队列 payload
  里已有 scope_id，但 worker 入口还没统一加 `scope(**payload_ctx)`。
  可在 PR-28 Subagent 状态机里顺便做掉（那里会做 worker 钩子的重构）。
- Queue Service dispatch 端点接到 session_id 后，主动 bind
  session_repo 查到的 scope_id（目前只从 Header 读）——优先级低，
  可等 PR-29。
