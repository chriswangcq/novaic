# Phase 2.3: Projection tool call/result placement

## Problem

Implement projection of assistant tool call and tool step events into LLM-compatible message order. This belongs under Phase 2 because tool results must be represented from events before read-path cutover can stop consulting legacy step files.

## Success Criteria

- Projector handles `AssistantToolCallRecorded` and `ToolStepRecorded`.
- Tool result messages are attached by `call_id` and preserve event order.
- Tool observation preview/summary data is included without fetching payload bytes.
- Orphan tool results without assistant call are still represented in a deterministic, loud/debuggable way.
- Tests cover assistant call + result, multiple tools, orphan result, and payload_ref preservation.
