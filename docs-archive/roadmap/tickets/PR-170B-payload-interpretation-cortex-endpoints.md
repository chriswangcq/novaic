# PR-170B — Payload Interpretation Cortex Endpoints

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-cortex`, docs |
| Parent | PR-170 |

## Goal

Add explicit Cortex endpoints that resolve payload refs under budget/redaction and call LLM Factory for summarize/QA.

## Current-State Analysis

Cortex owns payload storage and deterministic read/search endpoints. It does not yet expose interpretation endpoints or any Factory-backed interpretation path.

## Implementation Checklist

- [x] Add `PayloadSummarizeRequest` and `PayloadQARequest`.
- [x] Resolve payload text by ref with strict input budget.
- [x] Redact obvious secret-bearing text before interpretation.
- [x] Call LLM Factory only from explicit interpretation endpoint requests.
- [x] Return bounded result text and MCP text content.
- [x] Add Cortex endpoint tests with mocked Factory client.
- [x] Run Cortex tests.
- [x] Commit and push Cortex changes; update parent submodule pointer.

## Done Criteria

- No automatic payload summary path exists.
- Interpretation endpoint output is a new bounded observation result.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_payload_inspection_api.py tests/test_tool_schemas_limits.py tests/test_trace_projection.py`
- `PYTHONPATH=.:../novaic-common pytest -q`
- `python -m py_compile novaic_cortex/api.py novaic_cortex/trace_projection.py`
