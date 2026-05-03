# PR-188B — Agent Monitor Default Scope Guard

Status: `[closed]` — 2026-05-03

## Goal

Prevent the App-default Agent Monitor path from drifting back to `agent-root-main`.

## Current-State Analysis

The App intentionally does not know Cortex root scope ids. `ChatPanel` calls `useActivityTimeline(currentAgentId, ...)`, and the hook sends only `agent_id` unless a caller explicitly chooses a subagent.

That is the right boundary, but Business needs a regression test proving the default path resolves the real main subagent id.

## Implementation

- [x] Update the Activity Timeline Business test to assert omitted `subagent_id` resolves through the main subagent row.
- [x] Keep an explicit-subagent test to prove non-default callers still bypass main resolution.
- [x] Keep the App monitor guard unchanged: normal monitor uses Activity Timeline, not execution logs.

## Validation

```bash
PYTHONPATH=. pytest -q tests/test_pr169_activity_timeline_action.py
npm --prefix ../novaic-app run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/hooks/useActivityTimeline.test.ts
```

Result: passed.
