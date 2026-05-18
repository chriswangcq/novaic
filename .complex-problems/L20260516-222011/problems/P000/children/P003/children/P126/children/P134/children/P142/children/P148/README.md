# write_step_projection call-site boundary audit

## Problem

`write_step_projection` connects API/runtime tool observations to workspace step files. Even if lower-level workspace functions are correct, active call sites can still pass legacy inline shapes, skip payload externalization, or write projections without complete refs.

This child belongs under `P142` because the active wiring must prove new execution paths actually use the step normalization/index contract, not merely define it.

## Success Criteria

- Source pointers map all active `write_step_projection` call sites.
- Evidence proves call sites pass structured observation/percept data instead of raw inline result strings.
- Evidence proves call sites propagate `step_ref`/`payload_ref` and artifact metadata into the workspace layer.
- Tests cover at least one active projection path from tool result to step file/index row.
