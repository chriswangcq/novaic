# PR-144 — Prompt / Memory / Summary Residue Scan

| Field | Value |
| --- | --- |
| Status | `[scanned]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | business, cortex, runtime, common, docs |
| Depends on | PR-143 |

## Goal

Ensure Cortex continuity remains minimal: no automatic summary producer, no wake summary concept, no memory inference from chat replies, no user-profile ownership inside Cortex/Runtime.

## Scan Plan

1. [x] Search active code for summary producers and memory/profile inference.
2. [x] Verify prompt assembly ownership is Business-only.
3. [x] Verify `skill_end(report=...)` remains the only durable LLM-authored summary path.
4. [x] Separate doc archaeology from live prompt strings.

## Findings

- Cortex boundary guard passes: no active Cortex ownership violations for auto-summary, profile ownership, task proxying, notebook/search proxying, `wake summary`, or chat-reply memory inference.
- Runtime code comments and implementation preserve the intended path: structural wake finalization does not write durable summaries; LLM-authored durable summaries come from `skill_end(report=...)`.
- Business prompt assembly still injects product data:
  - `用户画像` from `drive.user_profile`.
  - `agent-notebook` summary through `_get_agent_notebook_summary`.
  - Prompt text can still mention profile/notebook continuity.
  - Business internal routes still include notebook, memory, tasks, and profile update actions.
- These are not Cortex contamination, but they can still confuse the Agent story because notebook/task tools are no longer exposed as LLM tools.

## Follow-up Decision

Keep Cortex minimal. Decide separately whether Business-owned profile/notebook/task product data should remain. If it remains, document it as product context, not Agent-autonomous memory.

## Unit / Guardrail Tests

- [x] Existing Cortex boundary guard passed.
- [ ] Add Business prompt ownership guardrail if profile/notebook wording is narrowed.

## Smoke / Deploy

- [x] No deploy for scan-only changes.
- [ ] Cleanup follow-up must smoke LLM context assembly.

## Git / Merge

- [ ] Commit ticket updates.
- [ ] Push parent docs update.
