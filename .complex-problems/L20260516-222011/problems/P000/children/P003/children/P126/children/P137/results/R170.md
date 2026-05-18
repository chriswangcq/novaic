# Active skill stack injection map result

## Summary

Closed the active-skill-stack injection split investigation. Active stack state is operational-store backed in Cortex; the final LLM-visible stack message is produced by common pure LLM assembly; current display media is keyed by round/tool metadata rather than message position; and no stale duplicate stack injection path was found.

## Done

- P180 mapped active stack source/projection and proved it is operational-store backed, not file-walk backed.
- P181 mapped final context injection ordering: common assembly appends the transient active stack system message after Cortex messages and before optional no-tool warning.
- P182 verified the current-display/media regression where a display result is followed by an active stack system message.
- P183 audited stale/duplicate injection paths and classified remaining matches as active, contract, or test-only.

## Verification

- Child success checks:
  - P180: C180
  - P181: C181
  - P182: C182
  - P183: C183
- Representative passing suites:
  - P180 active stack source/projection: `43 passed in 0.54s`.
  - P181 stack ordering/common assembly: `40 passed in 0.15s`.
  - P182 display regression coverage: `53 passed in 0.16s`.
  - P183 cleanup guards: common/runtime `24 passed in 0.10s`, Cortex `9 passed in 0.01s`.

## Known Gaps

- No correctness gap remains for active stack injection.
- Broader `context_stack` compaction cleanup is outside this active-stack injection map and should be handled separately if desired.

## Artifacts

- P180 result R166 and check C180.
- P181 result R167 and check C181.
- P182 result R168 and check C182.
- P183 result R169 and check C183.
- Primary implementation files:
  - `novaic-cortex/novaic_cortex/active_stack_projection.py`
  - `novaic-cortex/novaic_cortex/api.py`
  - `novaic-common/common/contracts/llm_assembly.py`
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
  - `novaic-agent-runtime/task_queue/contracts/llm_call.py`
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py`
