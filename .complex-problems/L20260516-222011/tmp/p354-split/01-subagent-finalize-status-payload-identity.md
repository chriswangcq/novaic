# Subagent finalize status payload identity

## Problem

`wake_finalize` currently builds `set_subagent_sleeping` and `set_subagent_completed` payloads from coarse `agent_id/subagent_id` only. Terminal Business status updates need explicit wake/session identity in their payloads so downstream handlers can reject malformed finalize tasks and tests can prove no legacy `last_scope_id` field is used.

## Success Criteria

- Inspect `task_queue/sagas/wake_finalize.py` status payload builders.
- Add explicit current finalize identity to both terminal-status payloads, including `scope_id` and positive `session_generation`.
- Preserve existing `agent_id/subagent_id` fields and `result` semantics for completed payloads.
- Do not add or reintroduce `last_scope_id`.
- Add focused tests proving both payload builders carry the new identity and reject missing/non-positive generation.

