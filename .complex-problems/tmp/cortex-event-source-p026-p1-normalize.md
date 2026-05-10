# Phase 3.4.1: Normalize tool step payloads before event emission

## Problem

`Workspace.write_step` currently mutates incoming step dictionaries by externalizing inline payloads and replacing `payload_ref`. Event emission needs the final normalized step data before writing `ToolStepRecorded`.

## Success Criteria

- A reusable normalization path produces final step data without hiding mutation inside legacy write-only code.
- Payload-bearing steps expose final `payload_ref` before event append.
- Existing validation rules for tool steps remain intact.
- Focused tests cover payload and non-payload steps.
