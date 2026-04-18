# PR-11 Business `_dispatch_trigger` 迁到 Assembler 调研与落地计划 (Preflight Review)

## 1. 目标与定位

本 PR 负责将 Business 微服务内部散落的两处 `_dispatch_trigger` (向 Queue Service 发送唤醒消息) 改为接入统一的 `DispatchAssembler`。
由于 `DispatchAssembler` 是在 PR-10 中新落地的标准入口，Business 将是它的第一个消费方。我们在此 PR 仅替换底层实现，保留 `_dispatch_trigger` 作为一层薄壳（Thin Shim），以维持对调用方无感知的渐进式重构（薄壳的删除将在 PR-18 进行）。

## 2. File:Line 落地与变更策略

| 文件路径 | 修改动作与目标 |
| --- | --- |
| `novaic-business/business/wake/assembler_factory.py` (新建) | **实例化工厂 (Blocker B)**：实现类似 PR-08 `get_resolver()` 的模块级工厂 `get_assembler()`，懒加载初始化 `AgentOwnershipResolver` 与 `DispatchAssembler`，避免挂载在不易获取的 `app.state` 上。 |
| `novaic-business/business/message_actions.py` | **替换薄壳**：由于 `assemble_and_dispatch` 是 async 的，而 `send_action` 原本是 sync def **(Blocker A)**，所以必须将 `send_action` 改为 `async def`（`main_business.py:302` 原生支持自动 `await`）。获取 `get_assembler()` 后，调用 `assemble_and_dispatch`。 |
| `novaic-business/business/internal/subagent.py` | **替换薄壳**：修改这里的 `_dispatch_trigger`，获取 `get_assembler()` 进行分发。 |
| `docs/roadmap/tickets/PR-11-business-trigger-to-assembler.md` | 更新状态。 |

### _dispatch_trigger 的调用分布 (Blocker D)
```bash
$ rg '_dispatch_trigger' novaic-business/
novaic-business/business/message_actions.py
48:def _dispatch_trigger(agent_id: str, user_id: str):
121:    _dispatch_trigger(agent_id, user_id)

novaic-business/business/internal/subagent.py
206:    _dispatch_trigger(
386:    _dispatch_trigger(
399:def _dispatch_trigger(agent_id: str, user_id: str, trigger_type: str, subagent_id: str = None, metadata: dict = None):
```
**声明**：可以看出，这里有两份独立的 `_dispatch_trigger` 实现，签名互不相同。本 PR 只做内部实现的替换，**保留各自签名互不合并**，真正的清理与合并将在 PR-18 进行。

## 3. TriggerType 映射与参数对齐 (Blocker C)

我们明确规定三种调用场景的元数据映射表：
- **User Message** (`message_actions.py:send_action`)：传入 `TriggerType.USER_MESSAGE`，必须传 `message_ids=[msg["id"]]`。
- **Subagent Send** (`subagent.py:206`)：传入 `TriggerType.SUBAGENT_SEND`，必须传 `message_ids=[msg["id"]]`。
- **Spawn Subagent** (`subagent.py:386`)：传入 `TriggerType.SPAWN_SUBAGENT`，必须传 `metadata={"initial_context": ...}`。

## 4. 测试策略

### 4.1 单测
- 在 `tests` 目录下（如 `novaic-business/tests/test_dispatch_shim.py`）通过 `monkeypatch` mock `get_assembler` 返回的 Assembler 实例，验证参数是否被正确拼装并喂给 `assemble_and_dispatch`。

### 4.2 本地集成回归
- 手工发一条消息确保不 500，且队列接收正常。
- 走 subagent 新建流程确保 Assembler 正确完成发送。

## 5. 日志与异常处理规范 (Fire-and-Forget 语义与 Blocker E)

在遇到 `DispatchError` 或其它网络异常时，为了维持 Fire-and-Forget 语义，我们只捕获并记录日志，不 `raise`。
为避免 silent failure，日志必须**完全结构化**：
```python
logger.error("event=dispatch_failed trigger=%s agent=%s kind=%s msg=%s", trigger_val, agent_id, e.kind, e.msg)
```
同时，在 `technical-debt.md` 记录 "silent dispatch failure 不可观测" 的风险，并在 `PR-32-metrics-prometheus-integration.md` 中增加 `dispatch_failed_total{caller=business}` 计数器作为兜底监控手段。
