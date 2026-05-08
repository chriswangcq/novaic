# P000: 补齐 FSM 基建 + 业务 DSL 全部 GAP

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
补齐 FSM 基建 + 业务 DSL 全部 GAP

## Success Criteria
- Generic FSM Runner 承接 Session/Task/Saga 共同 transition/outbox/projection 流程
- 业务 worker role/effect/action 进一步 DSL 化，旧 Python wiring/厚 engine 收薄或纳入清晰基建边界
- Cortex registry 不再从构造器隐式读取 env/time，依赖由 startup boundary 显式注入
- 旧命名/退休注释/transitional allowlist 清理到不会误导未来 agent
- 测试矩阵进入 CI 或等价强门禁，worker roster 具备单一 SSOT
- 全程删除旧路径，不保留向后兼容分支；所有新逻辑必须接入活路径并有守卫

## Subproblems
- P001: Generic FSM Runner 接入 Session/Task/Saga
- P002: Worker DSL 与 roster SSOT 收口
- P003: Cortex registry 显式依赖边界收口
- P004: 旧词汇、退休注释、transitional allowlist 清理
- P005: CI full matrix 与架构守卫门禁接入
- P006: 全局残留扫描与最终验证

## Results
- R007

## Latest Check
C008

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R007: problems/P000/results/R007.md
- Check C008: problems/P000/checks/C008.md

## Follow-ups
- none
