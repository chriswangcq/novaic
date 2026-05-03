# PR-190B — Guard Agent Monitor Entry Semantics

| Field | Value |
| --- | --- |
| Status | `[superseded]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app` |
| Parent | PR-190 |
| Superseded by | PR-191 |

## Goal

Prevent the Agent Monitor entry interaction from regressing into either a silent filter or the old diagnostic execution-log modal.

## Current-State Analysis

The App already has guards that keep `ExecutionLog`, `useLogs`, and raw `subagentsStore` out of `ChatPanel`, but they do not assert that participant selection opens Agent Monitor.

## Implementation Plan

- Extend the `ChatPanel` guard to require a named participant-select handler.
- Guard that the handler calls `setLogExpanded(true)`.
- Guard that `SubagentList` receives that handler.
- Keep the existing guards against `ExecutionLog`, `MainAgentLogPreview`, `useLogs`, and raw `subagentsStore`.

## Tests

- `src/components/Chat/ChatPanel.activityTimelineGuard.test.ts`
- `src/components/Visual/SubagentList.test.tsx`

## Done Criteria

- Tests fail if the bottom participant selector becomes a no-op filter again.
- Tests continue to fail if diagnostic execution log paths are reintroduced.

## Closure

Closed 2026-05-03.

Updated `ChatPanel.activityTimelineGuard.test.ts` to require:

- a named participant-select handler,
- `setSelectedParticipantId(participantId)`,
- `setLogExpanded(true)`,
- `onSelect={handleParticipantSelect}`,
- and no direct `onSelect={setSelectedParticipantId}` wiring.

`SubagentList.test.tsx` now verifies clicking the synthesized `Main Agent` participant still calls `onSelect('main')`.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/SubagentList.test.tsx
```

## Superseded

Superseded 2026-05-03 by [PR-191C — Guard Floating Layer Product Boundary](PR-191C-guard-floating-layer-product-boundary.md).

The guard should now protect floating-layer semantics rather than expand-on-click semantics.
