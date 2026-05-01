# PR-142 — Tool Schema / Executor Source Residue Scan

| Field | Value |
| --- | --- |
| Status | `[scanned]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | common, cortex, runtime, business, app |
| Depends on | PR-141 |

## Goal

Ensure LLM tool schemas, Runtime executors, Cortex tool exposure, Business-owned actions, and App rendering contracts have one clear ownership path. No phantom tool should be visible without a real executor.

## Scan Plan

1. [x] List canonical tool schemas from `novaic-common`.
2. [x] List Cortex-exposed tools.
3. [x] List Runtime executors.
4. [x] Compare App execution-log display contract against active tools.
5. [x] Search for old tool names and duplicated schema definitions.

## Findings

- Canonical `novaic-common` tool schemas, Cortex-exposed tools, and Runtime executors match:
  - `shell`
  - `skill_begin`
  - `skill_end`
  - `chat_reply`
  - `display`
  - `audio_qa`
  - `chat_history`
  - `subagent_spawn`
  - `subagent_send`
  - `sleep`
- App execution-log display contract covers the active tools through `novaic-common/common/contracts/execution_log_display.json`.
- No active LLM tool schema/executor exposure was found for removed tools such as `subagent_report`, `subagent_query`, or `subagent_cancel`.
- UI copy residue remains:
  - `novaic-app/src/locales/*/translation.json` still uses placeholder examples like `web_search, web_fetch, notebook_write`, which are phantom tools in the current system.
- Business still has internal task/notebook/memory routes. They are not currently exposed as LLM tools, but they can still confuse architecture ownership and should be handled by PR-144/product-boundary work.

## Follow-up Decision

Backend schema/executor ownership is clean. Follow-up should remove phantom tool examples from App i18n and keep a schema/executor parity guardrail.

## Unit / Guardrail Tests

- [x] Existing parity check confirms Common, Cortex, and Runtime alignment.
- [ ] Add App i18n guardrail if phantom tool examples are cleaned.

## Smoke / Deploy

- [ ] No deploy for scan-only changes.
- [ ] Cleanup follow-up must smoke `/v1/internal/tools` and at least one tool execution.

## Git / Merge

- [ ] Commit ticket updates.
- [ ] Push parent docs update.
