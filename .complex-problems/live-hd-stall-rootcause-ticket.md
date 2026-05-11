# Fix Cortex tool-result reference contract

## Problem Definition

The production wake failed after the HD screenshot tool step completed because the next `llm.call` could not resolve a tool result:

`Tool result not found: blob://cortex-payload/cpx-2d901bb3b40a91c28f3663ec70184dcf167e0017`

The Blob payload exists and is available in Cortex `payload_manifest`, with a stable source step ref:

`step-ref:f1c26fff-6141-4dc1-9702-69f4200fc2e8:round2:shell:1`

The suspected root cause is an implicit reference contract mismatch: event/projection code uses `payload_ref` as the LLM message `step_ref`, but formatted step lookup expects the durable step's `step_ref`.

## Proposed Solution

Make Cortex tool result references explicit and stable:

- Preserve both references when writing `ToolStepRecorded`:
  - `step_ref`: stable logical tool-step identifier used for step lookup.
  - `payload_ref`: concrete payload storage identifier, which may be a local step ref or a `blob://cortex-payload/...` ref.
- Project LLM tool messages with `message.step_ref = step_ref` when available.
- Preserve `payload_ref` in metadata for payload inspection and audit.
- Make formatted step lookup robust enough to locate a step by either `step_ref` or `payload_ref`, because both are durable identifiers for the same step.
- Add regression tests covering externalized Blob payloads flowing through event write, context projection, and formatted step read.

## Acceptance Criteria

- Externalized tool payload events include both stable `step_ref` and concrete `payload_ref`.
- Context projection emits stable `step_ref`, not a BlobRef, for LLM tool-result resolution.
- `steps_read_formatted` can resolve an externalized payload by stable step ref.
- Existing payload inspection by `payload_ref` remains valid.
- Tests fail before the fix and pass after the fix for the production failure mode.

## Verification Plan

- Run targeted Cortex tests for event write/projection/formatted step read.
- Run relevant runtime step-result-client tests if affected.
- Re-run a production or local smoke that exercises a shell/tool result followed by another LLM round.

## Risks

- Existing historical events may only have `payload_ref`; the projection must keep a safe fallback without making new events ambiguous.
- Overloading `step_ref` and `payload_ref` again would reintroduce this bug, so tests must assert both fields explicitly.

## Assumptions

- Blob payload externalization is intended and should remain.
- The stable source step ref is the correct identifier for LLM step-result lookup.
