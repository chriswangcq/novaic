# App Frontend And Factory Logs UI Cleanup

## Problem

Remove or narrow frontend/log UI residue that can expose raw payloads or mislead future agent work despite active chat/monitor paths being mostly clean.

## Success Criteria

- `novaic-llm-factory/static/factory-logs.html` applies safe client-side scrub/projection for raw request/response/message/tool detail rendering.
- Unused `novaic-app/src/components/Visual/SmartValue.tsx` is deleted if still unused.
- Legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx` is removed or narrowed so inactive paths cannot render raw JSON/base64/payload-like content.
- Focused frontend tests/lints pass for touched app surfaces.
