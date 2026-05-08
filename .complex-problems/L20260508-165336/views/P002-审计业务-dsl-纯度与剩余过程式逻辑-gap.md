# P002: 审计业务 DSL 纯度与剩余过程式逻辑 GAP

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
审计当前 worker assembly、action engine、effect adapter、business handler 是否达到“业务只剩 DSL”。需要区分基础设施 Python、合理 adapter Python、仍未 DSL 化的业务/协议控制流。

## Success Criteria
- 审计 `worker_assemblies.py` 的装配逻辑是否仍是手写 Python。
- 审计 task/saga/health/scheduler engines 是否仍有过程式控制流。
- 审计 EffectPlan 是否全面使用，是否还有边执行边 effect 的模式。
- 给出“不纯 DSL”的明确等级、影响和改造方向。
- 形成可执行 GAP 清单。

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
