# Cut Skill End Exception Diagnostics To Projection Snapshot

## Problem Definition

`context_skill_end` uses SQLite active-stack projection for normal `missing_scope_id`, `stack_empty`, `scope_mismatch`, and success decisions, but the exception branch still calls `_collect_active_stack(...)` to populate diagnostic response data. That leaves old file-walk stack authority in a core LIFO endpoint.

## Proposed Solution

Refactor `_context_skill_end_locked(...)` so its exception branch reuses the projection-derived `stack` captured at function entry:

- Keep the entry `read_active_stack_projection(...)` as the only stack source for `skill_end`.
- Remove the `_collect_active_stack(...)` fallback from the `except Exception` branch.
- Return `actual_stack_top` from `_stack_top_id(stack)` using the captured projection frames.
- Add a test that injects a close failure after projection read and monkeypatches `_collect_active_stack(...)` to fail, proving exception diagnostics do not walk files.
- Add/extend static guard for the `skill_end` section.

## Acceptance Criteria

- `_context_skill_end_locked(...)` contains no `_collect_active_stack(...)` calls.
- Exception response shape remains structured with `error_code="skill_end_exception"`, `requested_scope_id`, `actual_stack_top`, `stack`, and `stack_depth`.
- Existing missing, empty, mismatch, and success semantics remain unchanged.
- Targeted tests prove exception diagnostics use projection-derived stack data.

## Verification Plan

- Run targeted lifecycle/control-stack tests and read-source guard tests.
- Run static section check for `skill_end`.
- Run the full Cortex test suite.

## Risks

- Injecting an exception after projection read must target a stable failure point without changing production behavior.
- The exception branch should not attempt a second authority read; if projection read itself fails before `stack` exists, allowing the exception to propagate is acceptable because operational store is required.

## Assumptions

- Operational SQLite active-stack projection is required for `skill_end`.
- No file-walk fallback compatibility is needed.
