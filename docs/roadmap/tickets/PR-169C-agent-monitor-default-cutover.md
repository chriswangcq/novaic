# PR-169C — Agent Monitor Default Cutover

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app` |
| Parent | PR-169 |

## Goal

Make the normal Agent Monitor use Cortex Activity Timeline by default. Execution logs stop being a normal user-facing monitor source.

## Current-State Analysis

`ChatPanel` still imports `useLogs`, `ExecutionLog`, `MainAgentLogPreview`, and `SubagentList` for the normal monitor surface. Labels still say “Execution Log”. This keeps diagnostic execution data in the product path.

## Implementation Checklist

- [x] Switch ChatPanel preview and expanded monitor to Activity Timeline.
- [x] Rename user-facing labels from execution log to Agent Monitor / Activity.
- [x] Keep execution-log access only if explicitly placed behind a developer diagnostics surface.
- [x] Stop `MessageList.hasLogs` from being driven by execution-log rows.
- [x] Add tests/guards proving normal ChatPanel monitor path does not render `ExecutionLog`.
- [x] Run App tests/build.
- [x] Commit and push App changes; update parent submodule pointer.

## Done Criteria

- Normal monitor is Cortex-based.
- Message status remains delivery UI only.
- Execution logs no longer define the user's view of “Agent 在干活”.

## Verification

- `npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/ActivityTimeline.test.tsx src/components/hooks/useActivityTimeline.test.ts`
- `npm run build`
