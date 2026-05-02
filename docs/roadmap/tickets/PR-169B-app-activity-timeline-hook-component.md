# PR-169B — App Activity Timeline Hook and Component

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app` |
| Parent | PR-169 |

## Goal

Add a first-class App hook and user-facing component for Cortex Activity Timeline records.

## Current-State Analysis

The App has `useLogs()` and `ExecutionLog` components wired to Entangled `execution-logs`. Cortex records are already shaped as public timeline records, so App should map them directly into a small UI model rather than reinterpreting execution-log payloads.

## Implementation Checklist

- [x] Define `ActivityTimelineRecord` TypeScript shape.
- [x] Add `useActivityTimeline()` hook that calls `agents.activity_timeline`.
- [x] Add `ActivityTimeline` / record card component.
- [x] Render Observation / Reasoning / Action / Summary with user-facing language.
- [x] Ensure expanded state shows public `text` only, not debug payloads.
- [x] Add unit tests for mapping/rendering and debug-field non-rendering.
- [x] Run App tests/build.
- [x] Commit and push App changes; update parent submodule pointer.

## Done Criteria

- Activity Timeline can render without execution-log entities.
- The component is safe by construction: unknown raw fields are ignored.

## Verification

- `npm run test:unit -- src/components/hooks/useActivityTimeline.test.ts src/components/Visual/ActivityTimeline.test.tsx`
- `npm run build`
