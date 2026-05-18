# Audit payload write path and default context assembly boundary

## Problem Definition

Payload-heavy tool outputs must be written as durable payloads referenced by `step_ref`/`payload_ref`, while the normal LLM context assembly path must consume compact projections only. If any default context path reads full payload bodies, large shell/display output can re-enter model context as text or base64.

## Proposed Solution

Trace the write path from tool handler output through Cortex workspace/event storage, then trace the normal runtime context expansion path into LLM messages. Verify with targeted code inspection and tests that write-time storage records refs and that default expansion uses formatted projections/previews rather than full payload reads.

## Acceptance Criteria

- Tool/step write path evidence identifies where `step_ref` and `payload_ref` are created or preserved.
- Normal LLM context expansion path is mapped and shown not to call full payload read APIs by default.
- Large shell/display raw data is shown to stay behind durable payload/projection boundaries unless an explicit payload API is used.
- Focused tests covering write/projection/context paths pass.

## Verification Plan

Use `rg` and line-numbered reads over runtime tool handlers, Cortex workspace/event writer/projection code, and runtime context expansion code. Run focused Cortex/runtime tests for step write, event projection, shell projection, display/media boundaries, and runtime LLM message expansion.

## Risks

- The boundary crosses multiple packages, so a passing isolated test could miss a direct call path in another package.
- Some compatibility branches may still exist for old records; distinguish inactive historical compatibility from active default context assembly.

## Assumptions

- Explicit payload inspection APIs audited in `P228` are allowed and out of scope here.
- CLI/tool guidance exposure is handled by sibling problem `P230`.
