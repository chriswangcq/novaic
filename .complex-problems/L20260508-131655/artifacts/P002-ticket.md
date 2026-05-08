# P002 Ticket - 审计业务 DSL 与 worker assembly 厚度

## Problem Definition

审计当前 worker/handler 是否真正达到“组件层是通用员工，业务层只写状态机和具体计算逻辑”的目标。重点确认业务 DSL 厚度、worker assembly 是否统一、是否还有 raw constructor/plumbing 泄漏到业务层。

## Proposed Solution

只读检查以下内容：

- `task_queue/workers/assembly_helpers.py`
- `task_queue/workers/worker_assemblies.py`
- `task_queue/workers/*_effects.py`
- `task_queue/workers/task_execution.py`
- `task_queue/workers/saga_launch.py`
- `task_queue/workers/health_recovery.py`
- `task_queue/workers/scheduled_wake.py`
- worker registry 与相关测试。

通过 `rg`、`wc -l`、`sed` 和 targeted pytest 给出证据。

## Acceptance Criteria

- 说明 worker assembly 是否已统一到 helper/DSL 风格。
- 说明业务 handler 当前剩余厚度，给出代表性文件/行数/结构证据。
- 标出距离“业务只剩几行 DSL”的 gap。
- 验证 worker assembly / action engine 相关测试是否通过。

## Verification Plan

- 搜索 raw worker constructor 和 runtime plumbing。
- 读取 assembly helper、worker assembly、业务 handler/effects。
- 运行 worker assembly/action engine/handler cutover 测试。

## Risks

- 代码中存在合理的 adapter glue，不能把所有 glue 都误判成业务泄漏。
- “几行 DSL”是理想目标，审计要区分已达成、合理未达成、残留问题。

## Assumptions

- 本票只审计，不做代码修改。
