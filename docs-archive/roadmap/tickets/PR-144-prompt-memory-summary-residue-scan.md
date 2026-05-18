# PR-144 — Prompt / Memory / Summary Residue Scan

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
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

## Implementation

- Renamed LLM-visible profile injection from `## 用户画像` to `## 显式产品上下文`.
- Reworded continuity defaults so Business-owned product context is clearly auxiliary and not Cortex memory.
- Removed notebook ready-count injection from timed wake messages.
- Deleted the prompt-builder-local `_get_agent_notebook_summary` path; notebook summary remains an internal Business product endpoint, not a prompt-memory source.
- Added prompt guardrails forbidding old profile/notebook/wake-summary wording in the shared prompt contract and Business tests.

## Follow-up Decision

Keep Cortex minimal. Business-owned profile/notebook/task product data may remain only as product context; the LLM-visible prompt must not describe it as autonomous memory or Cortex continuity.

## Unit / Guardrail Tests

- [x] Existing Cortex boundary guard passed.
- [x] Added Business prompt ownership guardrail for product-context naming and no notebook wake injection.

## Smoke / Deploy

- [x] `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr111_system_prompt_builder.py tests/test_pr144_prompt_memory_boundary.py`
- [x] `PYTHONPATH=. pytest -q tests/test_tool_definitions_contract.py`

## Git / Merge

- [x] Implementation ready for commit in this batch.
- [x] Parent docs updated.
