# P001: Generic FSM Runner 接入 Session/Task/Saga

## Problem
Generic FSM Runner 接入 Session/Task/Saga

## Success Criteria
- Generic runner/substrate 承接重复 transition/state/outbox mechanics；至少一个活路径接入，且 Session/Task/Saga 重复代码减少或被统一 helper 管控
- 不得保留未使用 runner；必须有 tests/lints 证明活路径使用
