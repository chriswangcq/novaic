# PR-170A — Payload Interpretation Common Contracts

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, docs |
| Parent | PR-170 |

## Goal

Expose `payload_summarize` and `payload_qa` as canonical LLM-visible tool schemas and product semantics.

## Current-State Analysis

`payload_read` and `payload_search` are canonical in `common.tools.payload`, `AGENT_BUILTIN_TOOL_SCHEMAS`, `tool_product_semantics.json`, and `execution_log_display.json`. The interpretation tools are only mentioned as future roadmap text.

## Implementation Checklist

- [x] Add canonical schemas for `payload_summarize` and `payload_qa`.
- [x] Add product semantics entries with explicit-call wording.
- [x] Map both tools to a user-facing monitor kind.
- [x] Update schema/contract tests.
- [x] Run Common tests.
- [x] Commit and push Common changes; update parent submodule pointer.

## Done Criteria

- Common is the single source of truth for all four payload tools.
- Tool descriptions clearly reject hidden automatic summarization.

## Verification

- `PYTHONPATH=. pytest -q tests/test_payload_tool_schemas.py tests/test_tool_product_semantics_contract.py`
- `PYTHONPATH=.:../novaic-agent-runtime pytest -q`
