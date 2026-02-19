# Week 1 Task Order - Agent Runtime Team

## Team
Agent Runtime Team

## Mission
Split and stabilize workers runtime with clear throughput, retry, and idempotency controls.

## Scope
- Create `novaic-workers` repo
- Migrate `task_queue` and worker entrypoints
- Remove direct source coupling with gateway/runtime/tools repos
- Standardize retry policy and idempotency handling
- Validate independent worker execution

## Execution Plan (D1-D5)
- D1: Initialize repo and move workers/task_queue modules
- D2: Replace cross-repo imports with HTTP/API clients
- D3: Implement unified retry policy (backoff, max attempts, retryable errors)
- D4: Add idempotency guards and tests for duplicate task handling
- D5: Publish `v0.1.0-rc1` and operational runbook

## Acceptance Criteria
- Workers can run independently against configured service URLs
- Retry policy is code-enforced and documented
- Duplicate task execution does not produce duplicate side effects
- CI passes for unit and smoke integration tests

## Deliverables
- `novaic-workers` repo
- retry policy spec
- idempotency test set
- `v0.1.0-rc1` release + runbook

## Dependencies and Coordination
- Coordinate with API Team, Runtime Team, and Tools Team on client contracts
- Consume shared package from Platform Team

## Risk Escalation
- If throughput drops over 30 percent after migration baseline, escalate same day
