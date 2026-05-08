# Health/Scheduler Boundary Guards

## Problem Definition

Health and scheduler engines have been migrated to effect adapters, but the boundary needs automated tests. Without guardrails, future edits can reintroduce direct HTTP/client/assembler ownership inside action engines.

## Proposed Solution

Extend the PR-340 action-engine boundary test suite to cover `HealthRecoveryEngine` and `ScheduledWakeEngine`. Assert no concrete protocol imports, old constructor parameters, self-owned collaborator attributes, or direct collaborator calls. Also assert worker assembly wires health and scheduler effect adapters.

## Acceptance Criteria

- Boundary tests reject `httpx`/`internal_sync_client` imports in `health_recovery.py`.
- Boundary tests reject queue URL/internal-key constructor params and `_client` ownership in `HealthRecoveryEngine`.
- Boundary tests reject `business_client`/`assembler` constructor params and ownership in `ScheduledWakeEngine`.
- Boundary tests assert health/scheduler adapter wiring in worker assembly.
- Focused health/scheduler boundary suite passes.

## Verification Plan

- Run PR-340 boundary tests plus health/scheduler dispatch/generic worker tests.
- Compile worker modules.

## Risks

- Keep string checks specific so effect-name strings do not count as residue.

## Assumptions

- Adapter modules are allowed to import concrete clients/collaborators.
