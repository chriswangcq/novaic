# Ticket: Clean App Frontend And Factory Logs Payload Surfaces

## Problem Definition

Frontend and factory-log UI surfaces still contain raw JSON rendering paths that can expose large payloads, base64-like blobs, or legacy event structures after the backend/tool-output cleanup. This can mislead debugging and reintroduce context bloat through UI copy/paste or future agent work.

## Proposed Solution

Audit and remediate the three P786 surfaces as separate bounded work items:

- `novaic-llm-factory/static/factory-logs.html`: add or tighten client-side projection/scrubbing for request/response/messages/tool details so raw payloads are not blindly rendered.
- `novaic-app/src/components/Visual/SmartValue.tsx`: delete if unused; otherwise narrow it so it does not become a generic raw JSON/base64 renderer.
- `novaic-app/src/components/Chat/AssistantMessage.tsx`: remove or narrow legacy `events` rendering so inactive payload-like event paths cannot display raw JSON/base64 content.

## Acceptance Criteria

- Factory logs detail UI renders safe projections for raw request/response/message/tool detail views.
- `SmartValue.tsx` is physically deleted if unused, with imports/tests adjusted, or explicitly narrowed if a live use exists.
- `AssistantMessage.tsx` no longer has broad legacy event rendering that can surface raw payload content.
- Focused frontend tests/lints pass for touched surfaces.
- Residue scans prove no obvious raw base64/large JSON display path remains in these surfaces.

## Verification Plan

- Use `rg` to map all relevant raw rendering paths before editing.
- Split into child problems unless the audit proves the whole scope is smaller than expected.
- Run focused TypeScript/Vitest checks for touched app components where available.
- For factory logs HTML, run syntax/static checks and targeted text/projection tests if no browser build test exists.
- Re-run residue scans for `JSON.stringify`, base64-like render paths, `events`, raw request/response detail rendering, and stale payload wording in the scoped files.
