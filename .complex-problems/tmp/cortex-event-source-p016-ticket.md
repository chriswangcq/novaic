# Implement projection tool call/result placement

## Problem Definition

The projector handles messages and skill folds, but does not yet render assistant tool call events or tool step results. P016 must make tool observations event-driven before read-path cutover can stop consulting legacy step files.

## Proposed Solution

- Handle `AssistantToolCallRecorded` by appending its assistant message to the correct scope/root message stream and tracking tool call ids.
- Handle `ToolStepRecorded` by appending a deterministic `role=tool` message using `call_id`, `observation`, `payload_ref`, and status metadata.
- Use observation preview/summary as content when available; do not fetch payload bytes.
- Mark orphan tool results where no prior assistant call id was observed.
- Add tests for assistant call + result, multiple tools, orphan result, scoped tool result folded by skill close, and payload_ref preservation.

## Acceptance Criteria

- Assistant tool call messages are projected.
- Tool result messages preserve call_id and payload_ref metadata.
- Tool observations use explicit event payload only.
- Orphan results are deterministic and marked.
- Focused projection tests pass.

## Verification Plan

- Run projection/substrate tests.
- Static scan projector for payload file/Workspace/legacy DFS reads.

## Risks

- Existing LLM adapters may expect exact provider-specific tool message shape; keep output close to standard `role=tool`, `tool_call_id`, `content`.

## Assumptions

- Exact endpoint integration happens later; this ticket only defines pure projection behavior.
