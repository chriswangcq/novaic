# P010: Health and scheduler engines use effect adapters

## Problem
Health and scheduler engines use effect adapters

## Success Criteria
- HealthRecoveryEngine and ScheduledWakeEngine no longer hold direct HTTP/Business/assembler clients; adapters execute explicit effects
