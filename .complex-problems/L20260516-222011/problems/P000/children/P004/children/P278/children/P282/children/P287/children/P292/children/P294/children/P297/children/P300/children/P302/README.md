# Dispatch helper behavior test verification

## Problem

Run focused behavior tests proving the start-wake helper refactor did not regress queue session dispatch, attach, input consumption, suspected-dead recovery, or recovery outbox behavior.

## Success Criteria

- Focused pytest suite for pure FSM cutover, active inbox dispatch, attach outbox cutover, input consumption, suspected-dead recovery, and recovery outbox cutover passes.
- Any failure is classified as helper-related or pre-existing unrelated dirty-state with concrete evidence.
- No unrelated files are modified by the verification.
