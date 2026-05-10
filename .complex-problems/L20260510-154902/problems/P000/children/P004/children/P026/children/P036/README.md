# Phase 3.4.2: Wire steps/write to ToolStepRecorded events

## Problem

After normalization is explicit, `/v1/steps/write` must append `ToolStepRecorded` events for the active scope.

## Success Criteria

- `steps_write` appends `ToolStepRecorded` with target scope id.
- Event payload preserves call id, tool name, status, observation, and final payload ref.
- Legacy step files remain transitional.
- Focused tests verify event stream rows.
