# Week 1 Task Order - Runtime Team

## Team
Runtime Team

## Mission
Make runtime lifecycle orchestration independently operable with consistent state behavior.

## Scope
- Create `novaic-runtime-orchestrator` repo
- Migrate runtime orchestration modules and API routes
- Validate lifecycle transitions and consistency rules
- Add idempotency guards for repeated lifecycle operations
- Enable independent CI and release

## Execution Plan (D1-D5)
- D1: Initialize repo and migrate runtime orchestrator code
- D2: Define lifecycle state machine in docs and test baseline
- D3: Implement consistency protections (lock/idempotency/retry-safe transitions)
- D4: Integrate CI and fix migration regressions
- D5: Publish `v0.1.0-rc1` with lifecycle contract summary

## Acceptance Criteria
- Runtime service starts independently and passes health checks
- Repeated start/stop calls do not cause invalid states
- State query APIs behave deterministically
- CI passes on default branch

## Deliverables
- `novaic-runtime-orchestrator` repo
- lifecycle state model document
- test report for consistency scenarios
- `v0.1.0-rc1` release

## Dependencies and Coordination
- Align contracts with Platform Team
- Align callers with API Team and Agent Runtime Team

## Risk Escalation
- If state inconsistency is observed in repeated operation scenarios, escalate as P0
