# Backend Agent Progress Preview Payload Boundary

## Problem

Audit backend progress/event payload creation for agent monitor steps to ensure tool output summaries/previews are bounded and do not carry unredacted raw image bytes.

## Success Criteria

- Records exact scans for progress event, monitor event, step preview, and tool result payload creation.
- Cites backend slices showing bounded preview or payload-ref/manifest behavior.
- Separates backend monitor event payloads from LLM request context.
- Creates a follow-up if backend monitor events carry raw image bytes.
