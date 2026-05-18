# Child Problem: AssistantMessage legacy events rendering cleanup

## Problem

`novaic-app/src/components/Chat/AssistantMessage.tsx` contains legacy event rendering paths that may stringify non-string event content or render broad event payloads. Inactive legacy paths should not be able to display raw JSON/base64/payload-like content.

## Success Criteria

- Legacy `events` rendering is removed if no longer live.
- If a narrow event path is still required, it only renders safe, bounded text projections.
- `JSON.stringify` fallback rendering is removed or guarded for this chat surface.
- Focused chat/component tests pass for touched behavior.
