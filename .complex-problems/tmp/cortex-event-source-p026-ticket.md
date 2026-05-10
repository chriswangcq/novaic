# Cut tool step recording to events

## Problem Definition

`/v1/steps/write` still persists tool observations primarily as legacy `steps/*.json`, `steps/_index.jsonl`, and payload files. Tool results must become `ToolStepRecorded` ContextEvents without losing payload ref semantics.

## Proposed Solution

Split the work because tool writes combine payload normalization, active-scope resolution, and legacy step projection:

- Normalize step payload/payload_ref before event append so the event contains the final payload ref.
- Wire `/v1/steps/write` to append `ToolStepRecorded`.
- Preserve transitional legacy step files until cleanup.
- Audit remaining `steps/*` writes.

## Acceptance Criteria

- Tool step writes emit `ToolStepRecorded`.
- Event payload preserves final payload ref, call id, tool, status, observation, and target scope id.
- Payload-bearing steps use the final externalized payload ref in events.
- Focused tests and full Cortex tests pass.

## Verification Plan

- Add tests for simple tool step and payload-ref step.
- Run step/context event tests.
- Run full Cortex suite.

## Risks

- `Workspace.write_step` mutates the step payload today; event writing must not capture pre-normalized data.

## Assumptions

- Legacy step files remain transitional until P028.
