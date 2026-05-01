# PR-155 — Runtime Tool Executor Coverage Review

| Field | Value |
| --- | --- |
| Status | `[open]` |
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

- [ ] To be created after current-state analysis.

## Unit / Guardrail Tests

- [ ] Common schema contract test.
- [ ] Runtime executor coverage test.
- [ ] Cortex exposed-tool alignment test.
- [ ] Business product-tool route tests if touched.

## Smoke / Deploy

- [ ] Smoke representative native tools.
- [ ] Deploy affected services.
- [ ] Verify LLM `tools` array only contains supported tools.

## Git / Merge

- [ ] Each small ticket can be committed independently where practical.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark `[deployed]` only after deploy evidence is collected.
