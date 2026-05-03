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

The existing guard keeps `ExecutionLog`, `MainAgentLogPreview`, `useLogs`, and raw `subagentsStore` out of `ChatPanel`, but it still reflects PR-190's expand-on-click behavior.

## Implementation Plan

- Update the guard to require `ActivityTimelineModal`.
- Guard that `SubagentList` receives `onOpenParticipant`.
- Guard that direct `onSelect={setSelectedParticipantId}` and expand-on-click semantics are not used.
- Mark PR-190 as superseded by PR-191 so roadmap docs do not claim the old expand behavior as the current target.

## Tests

- `src/components/Chat/ChatPanel.activityTimelineGuard.test.ts`
- `src/components/Visual/SubagentList.test.tsx`
- `src/components/Visual/ActivityTimeline.test.tsx`

## Done Criteria

- Tests fail if the App returns to silent filtering, expand-on-click, or old execution-log modal behavior.

## Closure

Closed 2026-05-03.

Updated guard tests so `ChatPanel` must use `ActivityTimelineModal`, `handleParticipantOpen`, `setModalParticipantId(participantId)`, and `onOpenParticipant={handleParticipantOpen}`. Guards also reject direct `onSelect={setSelectedParticipantId}`, `setLogExpanded(true)`, and old diagnostic monitor imports.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/SubagentList.test.tsx src/components/Visual/ActivityTimeline.test.tsx
```
