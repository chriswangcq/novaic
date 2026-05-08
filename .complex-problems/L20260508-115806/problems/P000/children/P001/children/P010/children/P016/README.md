# P016: Scheduler engine effect adapter migration

## Problem
Scheduler engine effect adapter migration

## Success Criteria
- ScheduledWakeEngine owns no business client or assembler
- Due-agent scan and dispatch run through EffectExecutor
- Scheduler dispatch/generic worker tests pass
