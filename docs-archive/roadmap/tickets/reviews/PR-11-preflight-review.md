# PR-11 Preflight Review（Business → DispatchAssembler）

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **条件批准** — 补完 §A/§B 两个 blocker + §C/§D/§E 细节后直接进 T1 |
| 核心立场 | fire-and-forget 不抛外放行 ✅（junior §5 判断正确）但异步桥接 & 依赖注入路径没钉死 |

---

## §A（BLOCKER）`send_action` 是 sync，`assemble_and_dispatch` 是 async —— 必须显式说清怎么桥

### 现状
- `business/message_actions.py:79` `def send_action(store, user_id, params, payload)` **同步**
- `business/internal/subagent.py:176, 317` 两个 `async def` router handler **已经是异步**
- `main_business.py:302` 的 dispatcher 有这段：
  ```python
  result = handler(store, user_id, params, payload)
  if asyncio.iscoroutine(result):
      result = await result
  ```
  **已经支持 async handler**。

### 裁决
**把 `send_action` 改成 `async def`**，在内部 `await assembler.assemble_and_dispatch(...)`。dispatcher 已经能 await 返回的协程，零侵入。subagent.py 里两个 async handler 直接 await 新的 async `_dispatch_trigger`。

preflight 表格里**必须明文**写这条：
> `send_action` 从 `def` 改成 `async def`；`main_business.py:302` 的 `asyncio.iscoroutine(result)` 兜底路径负责 await，对外 API 行为不变。

**不要用 `asyncio.run()`**，会在已有事件循环里爆 `RuntimeError`。

## §B（BLOCKER）`app.state.assembler` 怎么到 sync-upgraded-to-async 的 `send_action` 里？

### 问题
`send_action(store, user_id, params, payload)` 签名**没有 request / app**。你写"挂到 `app.state.assembler`"但没给出 handler 怎么拿到这个 state。`entity_action` 的 `handler(...)` 调用根本没传 request。

### 两个可行方案（二选一，preflight 必须钉死）

**方案 1（推荐，与 PR-08 `get_resolver()` 一致）**：模块级 factory
```python
# novaic-common/common/wake/assembler.py 或 business/assembler_factory.py
_assembler_instance: Optional[DispatchAssembler] = None

def get_assembler() -> DispatchAssembler:
    global _assembler_instance
    if _assembler_instance is None:
        _assembler_instance = DispatchAssembler(
            resolver=get_resolver(),
            queue_base_url=os.environ["QUEUE_SERVICE_URL"],
            service_name="business",
        )
    return _assembler_instance
```
- `message_actions.py` / `subagent.py` 都 `from ... import get_assembler` 调用即可
- `main_business.py` startup 里**不需要**挂 `app.state`，factory 首次调用自动初始化
- 测试通过 monkeypatch `get_assembler` 注入 mock

**方案 2**：改 `entity_action` 把 request 传进 handler
- 需要改 dispatcher 签名（或 handler 签名加 `request=None` 可选参）
- 改动面更大，不推荐

**选方案 1，preflight 明文写"采用方案 1 (factory pattern)"**。

## §C（必做）三个 TriggerType 各自的 `message_ids` / `metadata` 必须显式写表

preflight §3 说"按需补充"太模糊。在源码里搜了一遍：

| 位置 | TriggerType | message_ids | metadata |
| --- | --- | --- | --- |
| `message_actions.py` `send_action` | `USER_MESSAGE` | `[msg["id"]]`（刚 `_store_add_message` 的返回值） | `{}` |
| `subagent.py:206` `subagent_send` | `SUBAGENT_SEND` | `[msg["id"]]`（刚 `store.append` 的返回值，`msg_id` 已在 `:192-204` 写入） | `{}`（可选透传 `sender_subagent_id`） |
| `subagent.py:386` `spawn_subagent` | `SPAWN_SUBAGENT` | `[msg["id"]]`（`:368` 写入的 SPAWN_SUBAGENT message） | `{"initial_context": initial_context}` |

这张表直接抄到 preflight §3，T1 实现时按行核对。

## §D（必做）preflight 少一条：grep 输出证明调用点穷举

Ticket 前置 checklist 明文要求 `rg '_dispatch_trigger' novaic-business/`。我本地跑了：

```
subagent.py:206   _dispatch_trigger(          ← call (subagent_send)
subagent.py:386   _dispatch_trigger(          ← call (spawn_subagent)
subagent.py:399   def _dispatch_trigger(...)  ← def
message_actions.py:48  def _dispatch_trigger(...)  ← def
message_actions.py:121 _dispatch_trigger(...)      ← call (user_message)
```

**3 个 call + 2 个 def，总共 5 处**。preflight §2 的 file:line 表里要包含这 5 处并在 T1 checklist 里一一勾。顺便写明：

> `message_actions._dispatch_trigger(agent_id, user_id)` 和 `subagent._dispatch_trigger(agent_id, user_id, trigger_type, subagent_id, metadata)` 是**两份独立实现、签名不同**。本 PR 各自替换、互不合并——保留 PR-18 再做统一删除。

## §E（必做）fire-and-forget 日志规范 + 技术债登记

§5 立场批准——**不 raise**是对的，保留原 API 稳定性。但加两个要求：

### E.1  结构化日志必须带全上下文
```python
except DispatchError as e:
    logger.error(
        "event=dispatch_failed via=assembler caller=business trigger=%s agent=%s kind=%s status=%s msg=%s",
        trigger_type, agent_id, e.kind, e.status, e.msg,
    )
```
避免用 `logger.error("dispatch failed: %s", e)` 这种短格式，后续 SIEM/ELK 解析要 key=value 对齐。

### E.2  登记 TD（必须）
在 `docs/roadmap/technical-debt.md` 加一条：

> **Business `_dispatch_trigger` 静默失败不可观测**：PR-11 保留 fire-and-forget 语义（不向外 raise），当 Assembler 返回 `DispatchError` 时只打 ERROR 日志。结果是"用户消息已落库 + 队列 dispatch 失败" 这个最坏路径外部不可感知（前端仍收到 200 OK）。后续 PR-32 metrics 集中治理时必须引入 `dispatch_failed_total{caller=business}` 计数器 + 告警。

在 PR-32 metrics ticket 里 backlog 一条对应条目。

## §F（信息性，不 block）注意一个 pre-existing bug-prone 语义

`send_action` 的顺序是：
1. `_store_add_message(...)` 写入 `messages` 表
2. `_dispatch_trigger(...)` 通知 Queue

如果步骤 2 失败，**数据库里有 USER_MESSAGE 但 agent 永远不醒**，前端不会得到任何错误反馈（200 OK）。本 PR **不修**这个问题，但日志必须明确到能通过 `kind` 判断出这类孤儿消息。后续（如 PR-26 Pending Alert）会有专门机制兜底。不要在本 PR 试图解决。

---

## 返工 checklist

- [ ] §A 在 preflight 明文写"send_action 改 async def + dispatcher 已支持 await"
- [ ] §B 选方案 1 factory pattern，preflight 写清楚 `get_assembler()` 放在哪、初始化时机、测试 monkeypatch 策略
- [ ] §C 把 3×TriggerType 的 message_ids / metadata 表直接贴到 preflight §3
- [ ] §D grep 输出贴到 preflight §2 + 明文声明"两份独立实现各自替换"
- [ ] §E.1 结构化日志格式字段对齐；§E.2 `technical-debt.md` 加 silent failure TD + PR-32 backlog
- [ ] PR-09 24h 观察期状态在消息里报一下

补完后不用再 review 一轮，直接进 T1。
