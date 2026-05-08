# P003: Cortex registry 显式依赖边界收口

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T004

## Problem
Cortex registry 显式依赖边界收口

## Success Criteria
- WorkspaceRegistry 构造器不再隐式 from_env/time.time；startup boundary 显式注入 policy/clock
- 新增/更新测试证明缺失依赖 fail-fast 或显式传入

## Subproblems
- none

## Results
- R003

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T004: problems/P000/children/P003/tickets/T004.md
- Result R003: problems/P000/children/P003/results/R003.md
- Check C004: problems/P000/children/P003/checks/C004.md

## Follow-ups
- none
