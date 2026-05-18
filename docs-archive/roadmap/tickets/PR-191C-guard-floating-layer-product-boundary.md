# PR-191C — Guard Floating Layer Product Boundary

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app`, docs |
| Parent | PR-191 |

## Goal

Prevent the floating layer from becoming the old diagnostic execution-log modal again.

## Current-State Analysis

The existing guard keeps `ExecutionLog`, `MainAgentLogPreview`, `useLogs`, and raw `subagentsStore` out of `ChatPanel`. It also needs to protect the floating-layer interaction directly.

## Implementation Plan

- Update the guard to require `ActivityTimelineModal`.
- Guard that `SubagentList` receives `onOpenParticipant`.
- Guard that direct `onSelect={setSelectedParticipantId}` and bottom-monitor expansion are not used for participant pills.

## Tests

- `src/components/Chat/ChatPanel.activityTimelineGuard.test.ts`
- `src/components/Visual/SubagentList.test.tsx`
- `src/components/Visual/ActivityTimeline.test.tsx`

## Done Criteria

- Tests fail if the App returns to silent filtering, bottom-monitor expansion, or old execution-log modal behavior.

## Closure

Closed 2026-05-03.

Updated guard tests so `ChatPanel` must use `ActivityTimelineModal`, `handleParticipantOpen`, `setModalParticipantId(participantId)`, and `onOpenParticipant={handleParticipantOpen}`. Guards also reject direct `onSelect={setSelectedParticipantId}`, `setLogExpanded(true)`, and old diagnostic monitor imports.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/SubagentList.test.tsx src/components/Visual/ActivityTimeline.test.tsx
```
