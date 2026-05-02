# PR-170D — Payload Interpretation End-to-End Guards

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-cortex`, `novaic-agent-runtime`, docs |
| Parent | PR-170 |

## Goal

Close PR-170 with cross-repo guards and smoke tests proving interpretation is explicit, bounded, and not a hidden summary path.

## Current-State Analysis

Read/search have existing integration tests. Summarize/QA need comparable cross-repo guardrails after schema, Cortex, and Runtime are wired.

## Implementation Checklist

- [x] Add tool-schema/executor/monitor contract guard covering all four payload tools.
- [x] Add smoke tests for explicit summarize/QA result shapes.
- [x] Confirm trace projection maps interpretation as observation.
- [x] Update architecture docs from future-tool wording to active-tool wording.
- [x] Run relevant full test suites.
- [x] Deploy services.
- [x] Commit and push parent docs/submodule pointers.

## Closure Notes

- Common schema/product-semantics tests cover all four payload tools.
- Runtime tool-path contract enforces schema/executor/monitor-name equality.
- Cortex endpoint tests cover explicit summarize/QA Factory call shapes, redaction, and output bounds.
- Cortex trace projection now has a guard that projects `payload_summarize` / `payload_qa` as user-facing semantic observations without leaking raw payload or `result_id`.
- The architecture document now describes `payload_summarize` / `payload_qa` as active explicit interpretation tools, not future placeholders.

## Verification

- `PYTHONPATH=.:../novaic-agent-runtime pytest -q` in `novaic-common`
- `PYTHONPATH=.:../novaic-common pytest -q` in `novaic-cortex`
- `PYTHONPATH=.:../novaic-common pytest -q` in `novaic-agent-runtime`
- `./deploy services`

## Done Criteria

- `payload_summarize` / `payload_qa` are active only through explicit tool calls.
- Docs, contracts, tests, and deployment all agree.
