# P013: Saga engine effect adapter migration

## Problem
Saga engine effect adapter migration

## Success Criteria
- SagaLaunchEngine owns no concrete Saga/Task clients
- Saga launch side effects run through EffectExecutor handlers
- Saga worker launch and boundary tests pass
