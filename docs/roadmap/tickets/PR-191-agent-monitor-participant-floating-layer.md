# PR-191 — Agent Monitor Participant Floating Layer

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app`, docs |
| Depends on | PR-188 |
| Supersedes | PR-190 |
| Theme | Agent Monitor floating participant surface |

## Goal

Restore the historical bottom participant pill interaction as a floating layer, while keeping the new Activity Timeline product data boundary.

## Current-State Analysis

Historical `SubagentList` behavior in `novaic-app` commit `01283c4` used `createPortal` and a fixed modal layer. Clicking a participant pill opened a centered overlay. That old overlay rendered `ExecutionLog` from `useLogs`, which is no longer acceptable for the normal user-facing Agent Monitor path.

PR-190 fixed the no-op click by expanding the bottom Agent Monitor. That made the click visible, but it did not match the desired product shape: the participant pill should open a floating layer.

## Big Work Items

- [x] [PR-191A — Activity Timeline Floating Layer Component](PR-191A-activity-timeline-floating-layer.md)
- [x] [PR-191B — Wire Participant Pills to Floating Layer](PR-191B-wire-participant-pills-to-floating-layer.md)
- [x] [PR-191C — Guard Floating Layer Product Boundary](PR-191C-guard-floating-layer-product-boundary.md)

## Required Process

For each small ticket:

1. Analyze current state.
2. Create or update the small ticket with the implementation plan.
3. Implement the smallest permanent change.
4. Run relevant unit tests/build checks.
5. Confirm the old diagnostic modal/raw log path does not return.

## Done Criteria

- Bottom Main Agent/Subagent pill opens a floating layer.
- The floating layer renders `ActivityTimeline` records, not `ExecutionLog`.
- The floating layer uses `agents.activity_timeline` product projection through `useActivityTimeline`.
- `SubagentList` remains presentation-only and does not read raw logs/subagents.
- Guard tests prevent silent filter wiring and old diagnostic modal resurrection.

## Closure

Closed 2026-05-03.

Implemented in `novaic-app`:

- Added `ActivityTimelineModal`, a portal-based floating layer that renders public Activity Timeline records.
- Changed `SubagentList` callback semantics from `onSelect` to `onOpenParticipant`.
- `ChatPanel` now tracks `modalParticipantId` and uses a dedicated `useActivityTimeline` call for modal content.
- PR-190 expand-on-click behavior is superseded; participant pill click now opens the floating layer.
- Existing guard still keeps `ExecutionLog`, `MainAgentLogPreview`, `useLogs`, and raw `subagentsStore` out of the normal user-facing path.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/SubagentList.test.tsx src/components/Visual/ActivityTimeline.test.tsx src/components/hooks/useActivityTimeline.test.ts
cd novaic-app && npm run build
cd novaic-app && rg -n "useLogs|ExecutionLog|MainAgentLogPreview|subagentsStore|onSelect=\\{setSelectedParticipantId\\}|setLogExpanded\\(true\\)|setModalSubagentId|logFilterStore|SubAgentMeta|SubAgentNode|execution-logs|SubSpec::new\\(\\s*\\\"subagents\\\"|SubSpec::new\\(\\s*\\\"execution-logs\\\"" src src-tauri/src ../novaic-common/common/contracts ../novaic-common/tests -S || true
```

Result: tests and build passed. The grep output contains only guard-test assertions.
