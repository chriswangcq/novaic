# PR-191A — Activity Timeline Floating Layer Component

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app` |
| Parent | PR-191 |

## Goal

Create a reusable floating layer for Agent Monitor participant activity.

## Current-State Analysis

`ActivityTimeline` is already the user-facing monitor surface. Historical floating UI used `createPortal`, backdrop, centered modal, and a close button, but rendered diagnostic execution logs.

## Implementation Plan

- Add an `ActivityTimelineModal` product component.
- Render through `createPortal`.
- Show participant label and activity count in the header.
- Render `ActivityTimeline` inside the modal body.
- Keep error/loading semantics delegated to `ActivityTimeline`.
- Do not render raw payload, result ids, or diagnostic transport details.

## Tests

- Modal renders title/records.
- Modal close button calls `onClose`.
- Modal does not render debug-only fields passed inside records.

## Done Criteria

- Floating layer exists without depending on `ExecutionLog`, `useLogs`, or raw subagent data.

## Closure

Closed 2026-05-03.

Added `ActivityTimelineModal` in `src/components/Visual/ActivityTimeline.tsx`. It uses `createPortal`, renders a backdrop and centered dialog, shows the participant label/activity count, and delegates loading/error/record rendering to `ActivityTimeline`.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Visual/ActivityTimeline.test.tsx
```
