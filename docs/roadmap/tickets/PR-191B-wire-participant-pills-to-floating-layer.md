# PR-191B — Wire Participant Pills to Floating Layer

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app` |
| Parent | PR-191 |

## Goal

Make bottom participant pills open the Activity Timeline floating layer.

## Current-State Analysis

`SubagentList` should expose an opening intent, not a silent filter intent. The target interaction is a floating layer scoped to the selected participant.

## Implementation Plan

- Rename the `SubagentList` callback to `onOpenParticipant`.
- In `ChatPanel`, track `modalParticipantId`.
- Clicking a pill sets selected participant and opens the modal.
- Use a dedicated `useActivityTimeline` call for the modal participant so the modal does not initially display stale main records.
- Keep the existing preview/expanded monitor data flow unchanged.

## Tests

- `SubagentList` click calls `onOpenParticipant`.
- `ChatPanel` source guard confirms modal state and callback wiring.

## Done Criteria

- Clicking `Main Agent` opens the floating layer.
- Clicking child participant opens the same floating layer scoped to that participant.

## Closure

Closed 2026-05-03.

`SubagentList` now exposes `onOpenParticipant`, and `ChatPanel` wires it to `handleParticipantOpen`. The handler selects the participant and opens the floating layer via `modalParticipantId`. Modal content is fetched by a dedicated `useActivityTimeline` call scoped to that participant.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Visual/SubagentList.test.tsx src/components/hooks/useActivityTimeline.test.ts
```
