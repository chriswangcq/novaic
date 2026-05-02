# PR-169D — Agent Monitor Debug Guardrails

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app`, docs |
| Parent | PR-169 |

## Goal

Prevent raw diagnostics from re-entering the normal Agent Monitor.

## Current-State Analysis

Previous UI iterations exposed `result_id`, raw MCP content, HTTP errors, and execution-log wording. Cortex projection already strips those fields; App should add static guardrails so future UI changes cannot accidentally reintroduce them.

## Implementation Checklist

- [ ] Add frontend guard tests for normal Activity Timeline components.
- [ ] Ban rendering of `result_id`, `_mcp_content`, raw HTTP body, stack trace, and “Execution Result” in normal monitor.
- [ ] Add source guard preventing ChatPanel normal monitor from importing execution-log components.
- [ ] Update PR-169 docs after closure.
- [ ] Run App tests/build.
- [ ] Commit and push App/doc changes; update parent submodule pointer.

## Done Criteria

- Debug payloads require a dedicated diagnostics surface.
- Normal user monitor remains product-language only.

