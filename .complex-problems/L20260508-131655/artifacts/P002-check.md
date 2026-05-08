# P002 Check - 业务 DSL 与 worker assembly 厚度

## Status

success

## Summary

P002 的审计目标已经完成。当前 worker lifecycle/component substrate 已统一，但业务代码还没有达到“只剩几行 DSL”的极致形态；主要剩余厚度在 `worker_assemblies.py`、`task_execution.py` 和 `scheduled_wake.py`。

## Evidence

- raw worker constructors 只出现在 `assembly_helpers.py`。
- business worker modules 由测试守卫禁止 lifecycle/protocol/client/runtime 泄漏。
- targeted worker/assembly/action-engine 测试 66 个全部通过。

## Criteria Map

- 说明 assembly 是否统一：已统一到 registry + assembly helper + process spec。
- 说明业务 handler 厚度：handler 已薄，protocol/action engine 仍厚。
- 标出 DSL gap：Python function wiring 和 action engine 分支仍未 DSL 化。
- 验证测试：66 passed。

## Execution Map

- 读取 assembly helper、registry、worker assemblies、handlers、engines、effect adapters、guard tests。
- 搜索 raw worker constructor。
- 运行 worker/DSL/cutover targeted tests。

## Stress Test

审计没有只看“是否有 GenericWorker”；还检查了 raw constructor 是否泄漏、handler 是否构造 protocol collaborator、registry 是否直接构造 handler、worker lifecycle token 是否残留。

## Residual Risk

目前是“组件层通用员工 + 业务层 action engine/handler”的形态，不是“业务只剩几行 declarative DSL”的最终形态。下一步若追求极致，需要继续抽出 action/effect binding spec、role wiring spec、decision/plan 小 DSL。
