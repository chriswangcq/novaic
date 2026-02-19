# Week 1 Task Order - Tools Team

## Team
Tools Team

## Mission
Make tools execution service independently deployable with reliability controls.

## Scope
- Create `novaic-tools-server` repo
- Migrate tools execution modules
- Define and implement timeout strategy
- Define and implement isolation/cleanup rules
- Add independent CI and release flow

## Execution Plan (D1-D5)
- D1: Initialize repo and migrate tools server code
- D2: Implement timeout policy (request timeout, execution timeout, global timeout)
- D3: Implement isolation controls and cleanup hooks for failed executions
- D4: Integrate CI and fix migration regressions
- D5: Publish `v0.1.0-rc1` and supported-tools matrix

## Acceptance Criteria
- Service runs independently and passes health checks
- Timeout behavior is deterministic and test-covered
- Failed tool runs leave no leaked process/resource state
- CI is green

## Deliverables
- `novaic-tools-server` repo
- timeout and isolation policy docs
- reliability test results
- `v0.1.0-rc1` release

## Dependencies and Coordination
- Coordinate with Storage-A/B for file/result APIs
- Coordinate with Runtime Team for runtime APIs
- Consume shared package and contracts from Platform Team

## Risk Escalation
- Any tool execution deadlock or resource leak is P0 and blocks release
