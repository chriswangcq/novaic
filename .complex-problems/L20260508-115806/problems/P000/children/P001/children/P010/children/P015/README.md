# P015: Health engine effect adapter migration

## Problem
Health engine effect adapter migration

## Success Criteria
- HealthRecoveryEngine owns no HTTP client construction
- Recover-all side effect runs through EffectExecutor
- Health dispatch/generic worker tests pass
