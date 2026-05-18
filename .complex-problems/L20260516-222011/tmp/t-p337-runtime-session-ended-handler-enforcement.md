# Runtime session-ended handler enforcement

## Problem Definition

Runtime/task handlers that process finalize/session-ended/skill-end/recovery completion are the last fail-closed boundary before Cortex or wake stack mutation. They must not infer current generation from active state or let stale tasks mutate Cortex, claim messages, close newer skills, or acknowledge unrelated work.

## Proposed Solution

1. Map all runtime/task handlers that process finalize/session-ended/skill-end/recovery completion and any outbox/runtime payloads they receive.
2. For each live handler, identify expected identity fields:
   - wake scope id
   - session generation
   - saga/runtime/task id where relevant
   - finalize reason
   - remaining stack / stack metadata where relevant
3. Verify or implement fail-closed checks before mutation:
   - missing expected scope/generation
   - stale scope
   - stale generation
4. Add focused tests proving stale handler calls do not mutate Cortex/wake state, claim unrelated messages, or close a newer skill.
5. Remove or classify handler paths that infer generation from current active state.

## Acceptance Criteria

- Runtime/session/finalize handler map is complete.
- Every live mutation handler has explicit identity checks or is documented as not mutating state.
- Missing/stale scope and generation paths are tested.
- Happy path remains tested.
- Upstream react generation defaults are resolved or explicitly assigned to the right child if they affect runtime finalize enforcement.

## Verification Plan

- Source inventory with `rg` over `task_queue/handlers`, `task_queue/sagas`, `task_queue/contracts`, `queue_service/session_*`, and tests.
- Focused tests for runtime handler enforcement and finalize ownership.
- Source guards for `session_generation or 0`, `current_session_generation` inference, and handler mutation without expected identity.

## Risks

- This is broader than P336 and likely not a safe one-go implementation. Split unless inventory proves it is tiny.

## Assumptions

- Backward compatibility for stale/missing runtime finalize identity is not required.
