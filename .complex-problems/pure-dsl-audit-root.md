# 全面排查当前代码与纯粹 DSL 目标的差距

## Problem

用户要求继续全面排查当前 Agent Runtime / Queue FSM / Worker DSL 架构是否已经达到“纯粹 DSL”目标。需要基于代码证据审计，而不是凭印象回答。审计范围包括：FSM substrate、worker command registry、runtime roster、worker assemblies、action engines、effect adapters、business handlers、deployment/startup wiring、CI guards、旧路径/兼容/残留分支。

本轮目标是审计与定位 GAP，不直接进行大规模重构。若发现问题，需要形成明确、可执行的后续工单清单，并区分：

- 已经 DSL 化/声明化的部分；
- 仍然是 Python 过程式逻辑但边界可接受的部分；
- 与“纯粹 DSL”目标冲突、需要继续改造的部分；
- 旧代码/兼容分支/未接入新逻辑的风险点。

## Success Criteria

- 逐项审计 runtime worker registry、roster、assembly、action engine、effect adapter、FSM runner、session/task/saga 入口是否走新路径。
- 给出代码证据指针，不泛泛而谈。
- 明确回答“现在是不是纯粹 DSL”，并说明差距等级。
- 列出完整 GAP 清单，每项包含影响、证据、建议修复方向、是否需要拆工单。
- 运行必要的 residue/guard/test 命令验证旧路径和守卫状态。
- 账本 valid/render/status/next 完成，审计问题达到 closed 状态。
