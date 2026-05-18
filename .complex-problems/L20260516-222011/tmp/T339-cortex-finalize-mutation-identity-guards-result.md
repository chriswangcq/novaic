# Cortex finalize mutation identity guards result

## Summary

Closed the split execution for P350 by solving all four child problems. The finalize mutation path now has explicit identity checks and propagation across Cortex scope-end, Session Coordinator finalization, and terminal SubAgent status mutation. Aggregate verification passed and found no remaining P350-owned stale finalize mutation hole.

## Done

- P353 / R333: hardened Cortex scope-end identity contract.
  - `handle_cortex_scope_end` requires `scope_id`, `agent_id`, `user_id`, and positive `session_generation` before archive.
  - The structural scope-end path remains keyed by explicit scope/root path and no longer acts as a summary-writing path.
- P354 / R338: hardened SubAgent terminal status mutation.
  - Terminal `set_sleeping` and `set_completed` payloads carry `scope_id` and positive `session_generation`.
  - Terminal handlers validate identity before Business `entity_update`.
  - Status flips are gated behind successful `session_ended`.
- P355 / R339: verified wake-finalize payload propagation.
  - Wake-finalize builders reject missing/zero generation.
  - Cortex scope-end, session-ended, sleeping, and completed payloads all carry the required finalize identity.
- P356 / R340: ran aggregate verification.
  - Focused aggregate test suite passed with `109 passed in 0.58s`.
  - Production residue search found no live `last_scope_id` / `last_scope_archived_at` propagation under `task_queue`.
  - No finalize generation zero-default compatibility branch was found in the inspected runtime paths.

## Verification

- Child checks all succeeded:
  - P353 latest check: C354
  - P354 latest check: C359
  - P355 latest check: C360
  - P356 latest check: C361
- Aggregate command evidence from R340:
  - `python3 -m py_compile ...` passed for touched finalize/session/subagent/FSM modules.
  - Focused pytest suite passed: `109 passed in 0.58s`.
  - `rg -n "last_scope_id|last_scope_archived_at" task_queue` returned no matches.
  - Business mutation search showed terminal status mutation paths are centralized in `task_queue/handlers/subagent_handlers.py`, where identity validation runs before `entity_update`.

## Known Gaps

- None for the P350 finalize mutation identity guard scope.
- Out of scope: broader recovery/compensation hazards not owned by P350.

## Artifacts

- P353 result/check: R333 / C354
- P354 result/check: R338 / C359
- P355 result/check: R339 / C360
- P356 result/check: R340 / C361
