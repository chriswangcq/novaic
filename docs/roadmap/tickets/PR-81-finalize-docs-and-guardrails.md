# PR-81 — Remove old rest/meta wording from active docs and guardrails

| Field | Value |
| --- | --- |
| Status | `[x]` done |
| Severity | P2 regression prevention |
| Owner | Codex |
| Branch | `codex/focus-new-llm-context` |

## Problem

Historical docs and shared metadata still mention `subagent_rest`, `wake summary`, `meta scope`, or old PREV paths. Some historical documents can remain as archives, but active contracts and tests must not teach the old model.

## Desired Contract

- Active docs describe only: agent-root, wake scope, child skills, active stack, `skill_end(report=...)`, `wake_finalize`.
- Shared common tests do not assume a `subagent_rest` LLM tool exists.
- Boundary guardrails catch old wording in active source and active docs.

## Implementation Checklist

- [x] Update active Cortex docs: builtin tools, call chain, lifecycle, invariants, API schema.
- [x] Update `novaic-common` wake-condition comments/tests to remove `subagent_rest` LLM-tool dependency.
- [x] Keep old roadmap tickets historical, but avoid using them as current contract.
- [x] Add/extend grep guardrails for active code/docs.

## Unit Tests

- [x] Common tests assert no `subagent_rest` tool is present.
- [x] Runtime/Cortex prompt contract tests assert no old rest/meta wording.
- [x] Cortex boundary tests keep blocking `wake summary` in active code.

## Smoke Test

- [x] Inspect latest LLM tool schema: no `subagent_rest`.
- [x] Inspect latest LLM context: no `meta-*` active scope and no `subagent_rest` instruction.

## Deployment

- [x] Deploy services touched by active prompt/code changes.

## GitHub / Commit Work

- [x] Commit `novaic-common` / docs changes.
- [x] Commit parent repo submodule pointers and tickets.
- [x] Push branches.
