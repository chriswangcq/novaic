# P012: Task engine effect adapter migration

## Problem
Task engine effect adapter migration

## Success Criteria
- TaskExecutionEngine owns no concrete Queue/Saga/Business clients
- Task execution side effects run through EffectExecutor handlers
- Task worker idempotency/retry/saga-parallel tests pass
