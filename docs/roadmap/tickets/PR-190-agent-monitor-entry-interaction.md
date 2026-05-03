# PR-190 — Agent Monitor Entry Interaction

| Field | Value |
| --- | --- |
| Status | `[superseded]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app`, docs |
| Depends on | PR-188 |
| Theme | Agent Monitor product interaction |
| Superseded by | PR-191 |

## Goal

Make the bottom Main Agent/Subagent participant control a real product entry point into Agent Monitor.

## Current-State Analysis

PR-188 correctly moved participant data behind `agents.activity_timeline`, but the App changed the bottom participant pill from the old "open logs modal" behavior into a silent local filter. The current click path calls only `setSelectedParticipantId(...)`; it does not open Agent Monitor, so clicking the currently selected `Main Agent` pill appears to do nothing.

This is not a transport or event-handler bug. It is an interaction semantics gap introduced during the monitor source-of-truth cleanup.

## Big Work Items

- [x] [PR-190A — Participant Selector Opens Agent Monitor](PR-190A-participant-selector-opens-agent-monitor.md)
- [x] [PR-190B — Guard Agent Monitor Entry Semantics](PR-190B-guard-agent-monitor-entry-semantics.md)

## Required Process

For each small ticket:

1. Analyze current state.
2. Create or update the small ticket with the implementation plan.
3. Implement the smallest permanent change.
4. Run relevant unit tests/build checks.
5. Confirm the old diagnostic modal/raw log path does not return.

## Done Criteria

- Bottom Main Agent/Subagent pill selects the participant and opens Agent Monitor.
- Clicking Main Agent is visible even when it is already selected.
- No old `ExecutionLog`, raw `subagents`, or modal diagnostic path returns to the normal user surface.
- Guard tests cover the intended interaction.

## Closure

Closed 2026-05-03.

Implemented in `novaic-app`:

- `ChatPanel` now handles participant selection through an explicit product handler.
- The handler selects the participant and expands Agent Monitor.
- `SubagentList` remains presentation-only and does not know layout state.
- Guard tests prevent regressing to direct `setSelectedParticipantId` wiring.

Validation:

```bash
cd novaic-app && npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/SubagentList.test.tsx src/components/Visual/ActivityTimeline.test.tsx src/components/hooks/useActivityTimeline.test.ts
cd novaic-app && npm run build
cd novaic-app && rg -n "useLogs|ExecutionLog|MainAgentLogPreview|subagentsStore|onSelect=\\{setSelectedParticipantId\\}|setModalSubagentId|logFilterStore|SubAgentMeta|SubAgentNode|execution-logs|SubSpec::new\\(\\s*\\\"subagents\\\"|SubSpec::new\\(\\s*\\\"execution-logs\\\"" src src-tauri/src ../novaic-common/common/contracts ../novaic-common/tests -S || true
```

Result: tests and build passed. The grep output contains only guard-test assertions, not live hot-path usage.

## Superseded

Superseded 2026-05-03 by [PR-191 — Agent Monitor Participant Floating Layer](PR-191-agent-monitor-participant-floating-layer.md).

PR-190 made the click visible by expanding Agent Monitor. Product direction was clarified afterward: the bottom participant pill should open a floating layer, matching the historical interaction shape, while still using Activity Timeline product projection instead of old diagnostic execution logs.
