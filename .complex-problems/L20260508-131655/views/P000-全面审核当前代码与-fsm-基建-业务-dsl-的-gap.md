# P000: 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap

## Success Criteria
- 覆盖 FSM substrate、业务 DSL/worker assembly、状态机接入、显式依赖边界、旧路径残留、测试与 CI 守卫
- 每个 gap 必须有文件/测试/命令证据，不能只凭印象
- 输出当前形态、已达成项、未达成 gap、风险和下一步建议

## Subproblems
- P001: 审计 FSM substrate 与状态机接入
- P002: 审计业务 DSL 与 worker assembly 厚度
- P003: 审计显式依赖边界与 side-effect adapter
- P004: 审计旧路径残留与兼容分支
- P005: 审计测试 CI 部署守卫覆盖

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R005: problems/P000/results/R005.md
- Check C005: problems/P000/checks/C005.md

## Follow-ups
- none
