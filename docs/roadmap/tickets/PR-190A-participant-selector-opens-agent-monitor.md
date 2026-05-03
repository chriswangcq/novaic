# PR-190A — Participant Selector Opens Agent Monitor

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app` |
| Parent | PR-190 |

## Goal

Make the bottom participant selector perform the user-visible action: select the participant and open Agent Monitor.

## Current-State Analysis

`SubagentList` calls `onSelect(view_id)` on click, and `ChatPanel` currently passes `setSelectedParticipantId` directly. That updates filter state only. If the clicked participant is already selected, especially `Main Agent`, the UI has no visible response.

## Implementation Plan

- Add a `ChatPanel` participant-select handler.
- The handler sets `selectedParticipantId`.
- The handler also calls `setLogExpanded(true)`.
- Keep `SubagentList` presentation-only; it should not import layout state or know how Agent Monitor opens.

## Tests

- Existing `SubagentList` tests still pass.
- Add/keep source guard verifying `ChatPanel` routes `SubagentList.onSelect` through an explicit handler rather than directly to `setSelectedParticipantId`.

## Done Criteria

- Clicking a participant opens Agent Monitor.
- Clicking already-selected `Main Agent` still opens Agent Monitor.

## Closure

Closed 2026-05-03.

`ChatPanel` now passes `handleParticipantSelect` to `SubagentList`. The handler calls both `setSelectedParticipantId(participantId)` and `setLogExpanded(true)`, so selecting the current `Main Agent` pill has a visible product effect.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/SubagentList.test.tsx
```
