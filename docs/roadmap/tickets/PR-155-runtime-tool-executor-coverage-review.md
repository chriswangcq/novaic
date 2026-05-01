# PR-155 — Runtime Tool Executor Coverage Review

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-common, novaic-agent-runtime, novaic-cortex, novaic-business, docs |
| Depends on | PR-154 |

## Goal

Confirm that every tool exposed by Common schema has a Runtime executor, clear product value, clear failure semantics, and aligned Cortex/Business/App behavior.

## Why This Matters

Tool schema is the LLM-facing contract. Exposing a tool without a real executor or product value creates hallucinated capability and old-path ambiguity.

## Required Process

For this big ticket:

1. Analyze the current live code and deployed behavior.
2. Create small implementation tickets for any concrete cleanup found.
3. Implement each small ticket one by one.
4. Confirm whether tool coverage is closed.
5. If not closed, return to step 3; otherwise close this ticket and move to PR-156.

## Boundary Invariant

- Common owns LLM tool schema.
- Runtime owns tool dispatch/executor mapping.
- Cortex owns scope/sandbox tools.
- Business owns product tools.
- Deleted/retired tools do not appear in LLM `tools`.

## Small Tickets

- [x] [PR-155A — Add Tool Schema / Executor / Monitor Contract Guardrail](PR-155A-tool-schema-executor-monitor-guardrail.md)

## Current-State Analysis

2026-05-02 scan found:

1. Common LLM-facing builtin schema exposes exactly: `shell`, `skill_begin`, `skill_end`, `chat_reply`, `display`, `audio_qa`, `chat_history`, `subagent_spawn`, `subagent_send`, `sleep`.
2. Runtime `_EXECUTORS` currently implements exactly the same names.
3. Cortex `TOOL_SCHEMAS` re-exports Common's `AGENT_BUILTIN_TOOL_SCHEMAS`; the existing Cortex tests pin this source-of-truth relationship.
4. Common already adapts `display`, `audio_qa`, `chat_history`, `subagent_spawn`, `subagent_send`, `sleep`, and `chat_reply` metadata from the canonical LLM schema. `notebook_*`, `task_*`, `subagent_report`, `subagent_query`, and `subagent_cancel` are not active builtin tools.
5. Runtime unit tests cover `display`, `audio_qa`, and `chat_history` product behavior and failure validation. Execution-log tests cover lightweight metadata and failure status.

The remaining gap is a single direct guardrail that pins Common schema names, Runtime executor names, and Agent Monitor display mapping names together.

## Closure

2026-05-02 PR-155A added the missing runtime-side invariant: Common `AGENT_BUILTIN_TOOL_SCHEMAS`, Runtime `_EXECUTORS`, and Common Agent Monitor `tool_display_kinds` must have exactly the same tool-name set. Targeted Runtime/Common/Cortex tool contract tests passed and Runtime was deployed.

## Unit / Guardrail Tests

- [x] Common schema contract test.
- [x] Runtime executor coverage test.
- [x] Cortex exposed-tool alignment test.
- [x] Business product-tool route tests if touched.

## Smoke / Deploy

- [x] Smoke representative native tools.
- [x] Deploy affected services.
- [x] Verify LLM `tools` array only contains supported tools.

## Git / Merge

- [x] Each small ticket can be committed independently where practical.
- [x] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [x] Mark `[deployed]` only after deploy evidence is collected.
