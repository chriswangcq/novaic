# P000: 补齐 FSM 基建 + 业务 DSL 全部 GAP

## Problem
补齐 FSM 基建 + 业务 DSL 全部 GAP

## Success Criteria
- Generic FSM Runner 承接 Session/Task/Saga 共同 transition/outbox/projection 流程
- 业务 worker role/effect/action 进一步 DSL 化，旧 Python wiring/厚 engine 收薄或纳入清晰基建边界
- Cortex registry 不再从构造器隐式读取 env/time，依赖由 startup boundary 显式注入
- 旧命名/退休注释/transitional allowlist 清理到不会误导未来 agent
- 测试矩阵进入 CI 或等价强门禁，worker roster 具备单一 SSOT
- 全程删除旧路径，不保留向后兼容分支；所有新逻辑必须接入活路径并有守卫
