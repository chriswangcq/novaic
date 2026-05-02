# PR-169C — Agent Monitor Default Cutover

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app` |
| Parent | PR-169 |

## Goal

Make the normal Agent Monitor use Cortex Activity Timeline by default. Execution logs stop being a normal user-facing monitor source.

## Current-State Analysis

`ChatPanel` still imports `useLogs`, `ExecutionLog`, `MainAgentLogPreview`, and `SubagentList` for the normal monitor surface. Labels still say “Execution Log”. This keeps diagnostic execution data in the product path.

## Implementation Checklist

- [ ] Switch ChatPanel preview and expanded monitor to Activity Timeline.
- [ ] Rename user-facing labels from execution log to Agent Monitor / Activity.
- [ ] Keep execution-log access only if explicitly placed behind a developer diagnostics surface.
- [ ] Stop `MessageList.hasLogs` from being driven by execution-log rows.
- [ ] Add tests/guards proving normal ChatPanel monitor path does not render `ExecutionLog`.
- [ ] Run App tests/build.
- [ ] Commit and push App changes; update parent submodule pointer.

## Done Criteria

- Normal monitor is Cortex-based.
- Message status remains delivery UI only.
- Execution logs no longer define the user's view of “Agent 在干活”.

