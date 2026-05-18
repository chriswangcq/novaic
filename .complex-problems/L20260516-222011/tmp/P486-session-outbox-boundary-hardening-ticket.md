# Session outbox dispatcher boundary hardening ticket

## Problem Definition

P486 must harden the sanctioned session side-effect outlet. `session_outbox.py` is allowed to turn durable session outbox rows into saga creation or queue publishes, but the codebase needs explicit tests/guards proving those session-owned effects do not leak into repository, routes, or other runtime paths.

## Proposed Solution

Inspect current session outbox guard tests and add or tighten focused guards if needed. The expected shape is: exactly one production `.saga_orchestrator.create(` for session-owned wake creation inside `session_outbox.py`, session-owned recovery/archive and attach publishes inside `session_outbox.py`, and repository/wake-plan code only building durable outbox effects rather than publishing. Run focused session outbox and wake/attach/recovery tests.

## Acceptance Criteria

- Session outbox dispatcher is documented as the required side-effect boundary.
- Tests/guards fail if session-owned saga creation moves outside the dispatcher.
- Tests/guards fail if repository/wake-plan paths directly publish session-owned effects.
- Focused session outbox/wake/attach/recovery tests pass.
- Any discovered bypass is removed or split into a smaller child problem.

## Verification Plan

Review and run existing guard tests such as session outbox required orchestrator, wake creation outbox cutover, attach outbox cutover, recovery outbox cutover, and session outbox effect boundary tests. Add missing guard coverage if current tests are insufficient.

## Risks

- Overly broad text guards can flag legitimate generic worker/queue infrastructure.
- Too-narrow guards may miss a new direct side-effect bypass outside the dispatcher.

## Assumptions

- Session outbox dispatcher itself remains the correct outlet for durable session side effects.
