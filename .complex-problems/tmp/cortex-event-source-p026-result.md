# Phase 3.4 tool step recording cutover result

## Summary

Completed the Phase 3.4 tool-step write cutover through three closed child problems: normalization (P035), `/v1/steps/write` event emission (P036), and boundary audit (P037). Tool observations now append `ToolStepRecorded` ContextEvents before writing transitional legacy step files.

## Done

- P035/R028: extracted `Workspace.normalize_step` so tool payload normalization is reusable, returns final payload refs, and avoids hidden caller mutation.
- P036/R029: wired `/v1/steps/write` to append `ToolStepRecorded` for the deepest active scope, preserving call id, tool, status, observation, and final payload ref.
- P036/R029: updated `ContextEventWriter.tool_step_recorded` so payload-less tool results do not require fake payload refs.
- P037/R030: audited remaining tool step write boundaries and found no direct-only tool-result bypass outside the new event path.
- Kept legacy step files as transitional projection/debug artifacts for later read-cutover/cleanup phases.

## Evidence

- Child success checks:
  - P035/C030
  - P036/C031
  - P037/C032
- Focused step event tests passed.
- Full Cortex suite passed after implementation: `445 passed`.
- Static scan found only `api.py:steps_write` as the runtime `write_step` caller; `steps_write` now emits `ToolStepRecorded` first.

## Residual Risk

- Legacy step readers and transitional file projections still exist by design; P005/P028 own read cutover and cleanup.
- Skill/scope lifecycle writes are not covered by this parent problem; P027 owns that next phase.
