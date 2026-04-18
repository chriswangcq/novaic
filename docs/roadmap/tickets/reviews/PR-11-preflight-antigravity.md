# PR-11 Business `_dispatch_trigger` 迁到 Assembler 调研与落地计划 (Preflight Review)

## 1. 目标与定位

本 PR 负责将 Business 微服务内部散落的两处 `_dispatch_trigger` (向 Queue Service 发送唤醒消息) 改为接入统一的 `DispatchAssembler`。
由于 `DispatchAssembler` 是在 PR-10 中新落地的标准入口，Business 将是它的第一个消费方。我们在此 PR 仅替换底层实现，保留 `_dispatch_trigger` 作为一层薄壳（Thin Shim），以维持对调用方无感知的渐进式重构（薄壳的删除将在 PR-18 进行）。

## 2. File:Line 落地与变更策略

| 文件路径 | 修改动作与目标 |
| --- | --- |
| `novaic-business/main_business.py` | **实例化依赖**：在 `lifespan` 阶段或启动时，初始化 `AgentOwnershipResolver` 与 `DispatchAssembler`，并挂载到 FastAPI 的 `app.state.assembler` 以供全局访问。 |
| `novaic-business/business/message_actions.py` | **替换薄壳**：修改 `_dispatch_trigger(agent_id, user_id)`，从中提取 `app.state.assembler`，并调用 `await assembler.assemble_and_dispatch(TriggerType.USER_MESSAGE, ...)`。由于原本是 fire-and-forget，捕获 `DispatchError` 记录 ERROR 日志但不 `raise`。 |
| `novaic-business/business/internal/subagent.py` | **替换薄壳**：修改 `_dispatch_trigger`（包含 `subagent_send` 和 `spawn_subagent` 两个场景），提取 `assembler` 并根据入参 `trigger_type` 转换为 `TriggerType` 枚举进行分发。同样捕获 `DispatchError` 记 ERROR 日志，不 `raise`。 |
| `docs/roadmap/tickets/PR-11-business-trigger-to-assembler.md` | 更新状态。 |

*(注：原 ticket 要求检查 PR-03 的 allowlist 中是否包含 `subagent.py`，经核实该 allowlist 仅为文档记录，且我们仅替换底层 HTTP 实现，暂不在此 PR 清理外部依赖。)*

## 3. TriggerType 映射与参数对齐

- **User Message (`message_actions.py`)**：原本硬编码发 `"user_message"`，将改传 `TriggerType.USER_MESSAGE`。
- **Subagent Send (`subagent.py:206`)**：入参传入 `"subagent_send"`，组装转换为 `TriggerType.SUBAGENT_SEND`。
- **Spawn Subagent (`subagent.py:386`)**：入参传入 `"spawn_subagent"`，组装转换为 `TriggerType.SPAWN_SUBAGENT`，并透传 `metadata={"initial_context": ...}`。

*(注：PR-09 已完成 `"user_response"` 到 `"user_message"` 的全局替换，因此不存在漂移的旧名称。)*

## 4. 测试策略

### 4.1 单测
- 在 `tests` 目录下（如 `novaic-business/tests/test_dispatch_shim.py` 或复用现有测试文件）通过 mock `app.state.assembler`，验证 `_dispatch_trigger` 是否正确转换参数并调用 `assemble_and_dispatch`。
- 断言：分别针对三种 TriggerType 断言 `assembler.assemble_and_dispatch.assert_called_with(...)` 的传参。

### 4.2 本地集成回归
- 手工发一条消息 (USER_MESSAGE) 确保不 500，且队列接收正常。
- 走 subagent 新建流程确保 Assembler 正确完成发送。
- 验证日志格式是否符合 PR-10 引入的 `event=dispatch trigger=... agent=... result=ok`。

## 5. 日志与异常处理规范 (Fire-and-Forget 语义)

Ticket 的示例如下：
```python
except DispatchError as e:
    logger.error("dispatch failed agent=%s trigger=%s kind=%s msg=%s",
                 agent_id, trigger_type, e.kind, e.msg)
    raise
```
**偏差修正/确认**：由于原本 `message_actions.py` 和 `subagent.py` 中都是直接 `logger.error(...)`（甚至直接吞），如果此处强制 `raise` 将会导致父级调用（如 `send_action` 和 `spawn_subagent` HTTP 接口）抛出 500 错误。
为了**严格遵守 "原调用方如果本来是 fire-and-forget，本 PR 保持一致"** 的指导思想，我将在捕捉到 `DispatchError` 时：
1. `logger.error(...)` 打印完整的结构化错误上下文。
2. **不抛出 (`raise`)**，以防止破坏已有 API 的稳定性。
*(若需要强制同步反馈抛出异常，请在 approve 时说明)。*
