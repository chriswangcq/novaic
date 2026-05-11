# Tool result step_ref projection repair

## Problem

Cortex event projection stores `ToolStepRecorded.payload_ref` only inside `_metadata.payload_ref`, but runtime LLM expansion requires a top-level `step_ref` on every tool message. This makes the next `react_think` fail before the LLM call.

## Success Criteria

- Projected tool messages include top-level `step_ref` equal to the event `payload_ref` when present.
- Existing metadata payload refs remain available for diagnostics.
- Regression tests prove normal, multiple, and orphan tool-result projections satisfy the runtime step-ref contract.
