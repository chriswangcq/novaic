# PR-154 — Agent Monitor User-Facing Review

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-app, novaic-agent-runtime, novaic-common, docs |
| Depends on | PR-153 |

## Goal

Confirm and enforce that the Agent Monitor shows user-facing activity language, not developer diagnostics. Result ids, raw MCP content, HTTP payloads, and debug-only factory details must not return to the normal monitor surface.

## Why This Matters

The monitor is a product surface: users should see the agent working. It is not a developer diagnostics panel unless a separate explicit diagnostic mode exists.

## Required Process

For this big ticket:

1. Analyze the current live code and deployed behavior.
2. Create small implementation tickets for any concrete cleanup found.
3. Implement each small ticket one by one.
4. Confirm whether the monitor surface is closed.
5. If not closed, return to step 3; otherwise close this ticket and move to PR-155.

## Boundary Invariant

- Runtime/Common define semantic display kinds and summaries.
- App renders semantic activity rows.
- Raw execution payloads are not default user-facing UI.
- Developer-only diagnostics, if retained, must be explicitly separate and not masquerade as the monitor.

## Small Tickets

- [ ] [PR-154A — Remove App Log Payload Diagnostic Path](PR-154A-remove-app-log-payload-diagnostic-path.md)

## Current-State Analysis

2026-05-02 scan found:

1. `LogCard` collapsed and expanded states already render semantic monitor language via `getExecutionLogDisplay`.
2. Existing component tests assert Factory ids, `result_id`, raw "Execution Result", and technical labels do not appear in the normal monitor surface.
3. Runtime/Common already emit `display_kind` / `display_summary`; Common has a shared `execution_log_display.json` contract and App tests compare against it.
4. Residue: App still contains an unused on-demand `log-payloads.get_payload` fetch/cache path (`logInputCacheStore`, `useLogs.fetchLogInput`, `entityToLogVM(...payload)`, and `log-payloads` app entity contract). The current UI does not call it, so it is dead diagnostic plumbing that could accidentally reintroduce raw payload display later.

## Unit / Guardrail Tests

- [ ] Add or update display contract tests for all monitor display kinds.
- [ ] Add frontend guardrails preventing raw ids/payloads in default monitor details.
- [ ] Confirm semantic labels exist for all Common tools.

## Smoke / Deploy

- [ ] Smoke a normal chat reply flow.
- [ ] Smoke at least one tool-using flow.
- [ ] Deploy affected services/app.

## Git / Merge

- [ ] Each small ticket can be committed independently where practical.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark `[deployed]` only after deploy evidence is collected.
