# Wake finalize status gating order

## Problem

The wake-finalize saga currently mutates Business subagent status before the session-generation-owned `session_ended` transition. If a finalize DAG is stale, Business status can be changed before the authoritative session state rejects the generation.

## Success Criteria

- Inspect the wake-finalize DAG definition and DAG executor dependency/failure behavior.
- Reorder or otherwise gate terminal subagent status tasks so `session_ended` acceptance happens before Business status mutation.
- Add tests proving the generated DAG order has `session_ended` before `set_subagent_sleeping` and `set_subagent_completed`.
- If executor semantics do not preserve the intended gate, split or fix that executor issue rather than relying on ordering by hope.
- Preserve Cortex scope_end ordering intentionally; document whether it remains before or moves after `session_ended`.

