# Runtime finalize handler inventory result

## Summary

Mapped runtime finalize/session-ended/skill-end/recovery completion paths. The important live mutation gaps are not just session-ended generation: `cortex.scope_end` archives scopes and marks notifications processed without checking current generation, and `subagent.set_sleeping` / `subagent.set_completed` mutate Business status with only agent/subagent identity. React contracts and recovery/compensation also need explicit generation treatment.

## Done

- Inventoried live finalize/session-ended/runtime paths:
  - `task_queue/sagas/wake_finalize.py`: builds `cortex.scope_end`, subagent sleeping/completed, and `session.ended` steps.
  - `task_queue/handlers/cortex_handlers.py::handle_cortex_scope_end`: archives Cortex scope, transitions input notifications to processed, removes bridge, marks participant completed.
  - `task_queue/handlers/cortex_handlers.py::handle_cortex_skill_end`: LLM/tool-driven skill close path; guarded by Cortex LIFO child scope id, not session generation.
  - `task_queue/handlers/subagent_handlers.py::handle_subagent_set_sleeping` and `handle_subagent_set_completed`: mutate Business subagent status with no wake scope or generation check.
  - `task_queue/handlers/session_handlers.py::handle_session_ended`: now validates positive generation before repository delivery.
  - `task_queue/contracts/react_think.py` and `task_queue/contracts/react_actions.py`: still default missing `session_generation` to zero and can feed wake-finalize context.
  - `queue_service/saga_repo.py`: compensation can synthesize wake-finalize contexts and suspected-dead events.
  - `queue_service/session_recovery.py`: recovery archive effect builds a Cortex scope-end effect from suspected-dead metadata.
- Classified implementation targets:
  - P349: remove/fix upstream react generation defaults.
  - P350: inspect/enforce identity guards for Cortex scope-end and Business status mutations, including subagent sleeping/completed.
  - P351: inspect/enforce recovery/compensation finalize identity preservation.
  - P352: aggregate verification.

## Verification

- Ran targeted `rg` over finalize/session-ended/skill-end/recovery terms in handlers, sagas, contracts, session recovery, and saga repo.
- Read source slices with `nl -ba` for:
  - `task_queue/handlers/cortex_handlers.py`
  - `task_queue/handlers/subagent_handlers.py`
  - `task_queue/handlers/runtime_handlers.py`
  - `queue_service/saga_repo.py`
  - `queue_service/session_recovery.py`

## Known Gaps

- `cortex.scope_end` and subagent status mutation paths do not currently validate expected generation against current root/session metadata.
- Recovery archive effect does not carry session generation into Cortex scope-end payload.
- React contracts still default `session_generation` to zero.

## Artifacts

- Source inventory evidence for P349-P352.
