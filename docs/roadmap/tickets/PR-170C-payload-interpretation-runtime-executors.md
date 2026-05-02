# PR-170C — Payload Interpretation Runtime Executors

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-agent-runtime`, docs |
| Parent | PR-170 |

## Goal

Wire `payload_summarize` and `payload_qa` LLM tool calls to Runtime executors that call Cortex interpretation endpoints.

## Current-State Analysis

Runtime has executors and bridge methods for `payload_read` / `payload_search` only. Tool result writing already records explicit tool results as Cortex observations, so interpretation results can reuse that path once executors exist.

## Implementation Checklist

- [ ] Add bridge methods for summarize/QA endpoints.
- [ ] Add Runtime executors with validation and bounded args.
- [ ] Fetch agent LLM config for interpretation calls.
- [ ] Add display summaries for monitor semantics.
- [ ] Update runtime tool path contract tests.
- [ ] Run Runtime tests.
- [ ] Commit and push Runtime changes; update parent submodule pointer.

## Done Criteria

- Explicit interpretation tool calls execute and become normal Cortex tool observations.
- Missing config, payload refs, or questions fail visibly and boundedly.
