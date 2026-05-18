# Runtime session-ended handler enforcement

## Problem

Runtime handlers receiving session-ended/finalize tasks must enforce expected wake scope and generation before mutating Cortex, claiming messages, archiving stack, or notifying queue state. Handler-side checks are the final fail-closed boundary if stale outbox or worker delivery occurs.

## Success Criteria

- Map runtime/task handlers that process session-ended/finalize/skill-end/recovery completion.
- Verify handlers compare expected scope/generation against current root/session metadata before mutation.
- Add or identify tests for missing expected scope, missing expected generation, stale scope, stale generation, and happy path.
- Ensure stale handler calls do not append Cortex input, close a newer skill, or acknowledge/claim unrelated messages.
- Remove or flag handler paths that infer generation from current active state.

## Belongs Under

This is the downstream runtime boundary for T324/P328; it protects Cortex and wake stack mutation from stale finalize tasks.
