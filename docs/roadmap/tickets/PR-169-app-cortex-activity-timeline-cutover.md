# PR-169 — App Cortex Activity Timeline Cutover

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app`, `novaic-cortex`, docs |
| Depends on | PR-166, PR-168 preferred |
| Theme | Agent Monitor source of truth |

## Goal

Make the default Agent Monitor consume Cortex Activity Timeline projection instead of using `execution-logs` as the user-facing source.

## Current-State Analysis

Cortex `/v1/trace/project` now returns safe user-facing records. App Monitor still renders the realtime Entangled `execution-logs` stream and adds phase labels locally. That is acceptable as a bridge, but it keeps execution logs doing product-surface work.

## Small Tickets

- PR-169A — App client and hook for Cortex Activity Timeline projection.
- PR-169B — Agent Monitor renders Cortex projection by default.
- PR-169C — Execution log moves to explicit developer diagnostics only.
- PR-169D — Guard normal user monitor against execution-log/result-id fallback.

## Done Criteria

- Normal monitor source is Cortex projection.
- Execution logs are diagnostic-only.
- Message status remains delivery UI only.
- No result id, raw MCP content, raw HTTP payload, or stack trace appears in normal monitor.
