# Diagnose device tool mount gap

## Problem Definition

小马 is expected to receive device tools, but recent LLM tool arrays do not include `hd_*`, `mobile_*`, or VM device tools.

## Proposed Solution

Trace the full device-tool path from persisted binding to Business filtering, Runtime/Cortex schema assembly, production prepared-context task outputs, and Runtime executor routing.

## Acceptance Criteria

- Confirm whether 小马 has a persisted device binding.
- Confirm whether Business can compute device tools from that binding.
- Confirm whether the production LLM context includes those tools.
- Confirm whether Runtime can execute those tools if exposed.
- Identify the exact architectural/code boundary causing the gap.

## Verification Plan

- Read the relevant source files with stable file pointers.
- Query production persisted binding and recent queue prepared-context outputs.
- Compare Business `/builtin-tools` output with Cortex/Runtime prepared tools.
- Check Runtime executor table for matching device tool handlers.

## Risks

- Production internal endpoints may require internal auth; if so, use DB and queue task evidence.
- Tool count can coincidentally match while the tool names differ, so compare names rather than totals.

## Assumptions

- 小马 agent id is `822af016-31a1-49bb-b529-9b8f539a0831`.
- The desired device binding is host desktop unless production data shows otherwise.
