# PR-188B — App Consumes Activity Timeline Participants

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app` |
| Parent | PR-188 |

## Goal

Make the bottom Agent/Subagent selector consume `participants` from `useActivityTimeline()`.

## Current-State Analysis

The current stopgap renders a main-only `SubagentList` and does not query raw `subagents`. This avoids breaking dev, but it is not the final product behavior.

## Implementation Plan

- Add `ActivityTimelineParticipant` TypeScript type.
- Normalize `participants` from `agents.activity_timeline` using a public-field allowlist.
- Return `participants` and `selectedParticipantId` from `useActivityTimeline`.
- Change `SubagentList` to render participant shape, not raw `SubAgentMeta`.
- Change `ChatPanel` selection state to call `useActivityTimeline(..., { subagentId })` and feed returned participants back into the selector.

## Tests

- Normalizer keeps only participant public fields.
- Hook passes selected participant/subagent id to Business.
- `SubagentList` renders main and child participants from activity timeline data.
- `ChatPanel` uses `SubagentList` without `useLogs` or raw `subagentsStore`.

## Done Criteria

- Bottom selector shows participants from the same product action as Agent Monitor.
- No App component imports raw `subagentsStore`.

## Closure

Closed 2026-05-03.

Implemented in `novaic-app`:

- Added `ActivityTimelineParticipant` type.
- `useActivityTimeline()` normalizes participants through a public-field allowlist.
- `SubagentList` renders participants rather than raw subagent rows.
- `ChatPanel` uses timeline participants and selected participant state.

Validation:

```bash
npm run test:unit -- src/components/hooks/useActivityTimeline.test.ts src/components/Visual/SubagentList.test.tsx src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/ActivityTimeline.guard.test.ts src/components/Visual/ActivityTimeline.test.tsx src/data/entities/entangledEntityContracts.test.ts
npm run build
```
