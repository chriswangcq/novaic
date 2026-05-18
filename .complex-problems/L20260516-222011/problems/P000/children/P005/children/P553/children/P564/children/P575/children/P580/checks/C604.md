# P580 Check

## Summary

Not successful. The inventory correctly proves public display tool history strips image bytes, but the strict review found a deeper boundary violation: display still persists small image bytes as inline base64 in `durable_payload.llm_content`. That is durable duplicated media state outside Blob Service, so this cannot be closed as clean.

## Evidence

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:142-164` builds `durable_payload.llm_content` from the raw display result.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:257-263` attaches that durable payload to the tool result.
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py:95-101` explicitly asserts the public content strips image bytes but durable payload still stores `_mcp_content[0]["data"]`.
- `novaic-common/common/contracts/blob.py:1-5` states Blob Service owns bytes and product services should persist BlobRef plus domain semantics.

## Gap

Display’s public text contract is good, but durable payload storage is not yet at the clean BlobRef-owned-byte boundary. This is a real optimization/fix candidate, not a cosmetic issue.

## Required Follow-Up

Create a follow-up to replace durable display image bytes with BlobRef-backed perception fetch while preserving current-turn LLM image delivery.
