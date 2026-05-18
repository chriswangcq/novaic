# P350 finalize mutation identity guards check

## Summary

Success. R341, backed by child results R333/R338/R339/R340 and checks C354/C359/C360/C361, satisfies the P350 problem. The runtime finalize mutation path no longer relies on stale `last_scope_*` transport or missing-generation compatibility, and each mutating path has explicit identity propagation and validation before mutation.

## Evidence

- P353 closed Cortex scope-end identity: `handle_cortex_scope_end` validates positive `session_generation` before archive and uses explicit scope/root path identity.
- P354 closed SubAgent terminal mutation identity: terminal handlers require `scope_id` and positive `session_generation` before Business `entity_update`, and status tasks are gated by `session_ended`.
- P355 closed wake-finalize payload propagation: all finalize mutation builders carry required identity and reject missing/zero generation.
- P356 aggregate verification passed:
  - compile passed for touched finalize/session/subagent/FSM modules.
  - focused tests passed with `109 passed in 0.58s`.
  - production `task_queue` search found no `last_scope_id` / `last_scope_archived_at` residue.
  - source search found no finalize generation zero-default branch in inspected runtime paths.

## Criteria Map

- Inspect `task_queue/handlers/cortex_handlers.py`, related bridge code, and tests: satisfied by P353 and P356 direct inspection.
- Verify scope/generation identity is checked before `scope_end`, stack archive, input append, or message acknowledgement: satisfied by Cortex `scope_end` positive generation validation before archive/ack flow, plus wake-finalize payload generation tests.
- Add tests for missing/stale scope and generation if a mutating path lacks coverage: satisfied by P353/P354/P355 tests that reject missing/zero generation and prevent terminal Business mutation before identity validation.
- If Cortex mutation is structurally keyed by scope path rather than session generation, document why safe or add the missing check: missing generation is no longer accepted; the implementation added explicit positive generation checks rather than relying only on structural scope path.

## Execution Map

- Split child P353 handled the Cortex scope-end mutation.
- Split child P354 handled Business SubAgent terminal status mutation.
- Split child P355 handled wake-finalize payload propagation into all mutating tasks.
- Split child P356 recomposed the path and verified tests/searches across the aggregate surface.

## Stress Test

Reviewed the parent solution against the stale finalize failure mode: an old finalize task should not be able to archive/ack a newer wake or flip a live subagent to sleeping/completed. The fix blocks that path at three layers: payload builders require generation, handlers validate generation before mutation, and status tasks cannot run after a rejected `session_ended`.

## Residual Risk

- Non-blocking: recovery/compensation logic outside P350 may still have its own hazards, but it is not part of the Cortex finalize mutation identity guard problem.
- Non-blocking: `subagent_wake.py` optional generation propagation is wake-start behavior, not a finalize mutation path.

## Result IDs

- R341
