# PR-170B — Payload Interpretation Cortex Endpoints

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-cortex`, docs |
| Parent | PR-170 |

## Goal

Add explicit Cortex endpoints that resolve payload refs under budget/redaction and call LLM Factory for summarize/QA.

## Current-State Analysis

Cortex owns payload storage and deterministic read/search endpoints. It does not yet expose interpretation endpoints or any Factory-backed interpretation path.

## Implementation Checklist

- [ ] Add `PayloadSummarizeRequest` and `PayloadQARequest`.
- [ ] Resolve payload text by ref with strict input budget.
- [ ] Redact obvious secret-bearing text before interpretation.
- [ ] Call LLM Factory only from explicit interpretation endpoint requests.
- [ ] Return bounded result text and MCP text content.
- [ ] Add Cortex endpoint tests with mocked Factory client.
- [ ] Run Cortex tests.
- [ ] Commit and push Cortex changes; update parent submodule pointer.

## Done Criteria

- No automatic payload summary path exists.
- Interpretation endpoint output is a new bounded observation result.
