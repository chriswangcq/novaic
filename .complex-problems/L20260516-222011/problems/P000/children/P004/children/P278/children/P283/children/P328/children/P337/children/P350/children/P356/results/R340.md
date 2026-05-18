# Finalize mutation guard aggregate verification result

## Summary

Completed the P356 aggregate verification pass over the P350 finalize mutation guard work. No production code was changed in this ticket. The aggregate evidence shows the composed wake-finalize path now carries explicit scope identity and positive generation into Cortex scope-end, Session Coordinator finalization, and terminal SubAgent status mutation, and the terminal status tasks are gated behind successful `session_ended`.

## Done

- Ran Python compilation over the touched finalize/session/subagent/FSM contract modules:
  - `task_queue/sagas/wake_finalize.py`
  - `task_queue/saga.py`
  - `task_queue/dag_builder.py`
  - `task_queue/workers/task_sources.py`
  - `task_queue/handlers/session_handlers.py`
  - `task_queue/handlers/subagent_handlers.py`
  - `task_queue/handlers/cortex_handlers.py`
  - `task_queue/contracts/session_generation.py`
  - `task_queue/contracts/react_think.py`
  - `task_queue/contracts/react_actions.py`
- Ran the focused aggregate pytest suite covering Cortex scope-end, wake finalize payload builders, SubAgent terminal status handlers, session finalization ownership, DAG dependency behavior, and related runtime guardrails.
- Ran residue searches for retired finalize mutation fields and unsafe generation fallback patterns.
- Inspected production mutation paths:
  - `wake_finalize.py` lines 25-40, 43-60, 71-79, 98-109, 112-143.
  - `subagent_handlers.py` lines 62-69, 71-112, 115-156.
  - `session_handlers.py` lines 14-27, 30-90.
  - `cortex_handlers.py` lines 63-80 and 98-168.
- Mapped P350/P356 criteria to evidence:
  - Cortex scope-end identity: `handle_cortex_scope_end` requires `scope_id`, `agent_id`, `user_id`, and positive `session_generation` before archive.
  - SubAgent terminal mutation identity: `set_sleeping` and `set_completed` require `scope_id` and positive `session_generation` before `entity_update`.
  - Wake-finalize payload propagation: builders reject missing/zero generation and propagate scope/generation into Cortex, Session, and terminal status payloads.
  - Finalize ownership: `session_ended` validates positive `generation`, forwards reason/generation/remaining stack, and rejects `finalize_rejected` as a task-gating failure.
  - DAG composition: terminal status tasks explicitly depend on `session_ended`.

## Verification

- `python3 -m py_compile ...` exited successfully for all listed modules.
- Focused aggregate test suite:

```text
109 passed in 0.58s
```

- Retired-field production search:

```text
rg -n "last_scope_id|last_scope_archived_at" task_queue
# no matches
```

- Broader test search found only retirement assertions and intentional legacy-noise inputs in tests:

```text
tests/test_pr43_last_scope_wiring.py
tests/test_pr43_previous_scope_transport.py
```

- Generation fallback search found no `ctx.get("session_generation") or 0`, `payload.get("session_generation") ... or`, or equivalent zero-default compatibility branch in the finalize mutation paths. The only optional `ctx.get("session_generation")` production hit is `task_queue/sagas/subagent_wake.py`, which is wake-start propagation rather than the P350 finalize mutation path.
- Business mutation search shows the only `entity_update` calls in `task_queue/handlers` are the SubAgent status handlers; terminal status handlers are guarded before mutation.

## Known Gaps

- None for the P350-owned finalize mutation guard path.
- Deliberately out of scope: sibling recovery/compensation hazards outside finalize mutation ownership. Those must remain under their own problem packages rather than being implied solved by this aggregate verification.

## Artifacts

- Ledger ticket: `.complex-problems/L20260516-222011/tmp/P356-finalize-mutation-guard-aggregate-verification-ticket.md`
- This result body: `.complex-problems/L20260516-222011/tmp/T347-finalize-mutation-guard-aggregate-verification-result.md`
