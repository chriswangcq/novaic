# PR-170 — Payload Interpretation Tools

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-agent-runtime`, `novaic-cortex`, `novaic-llm-factory`, docs |
| Depends on | PR-164 |
| Theme | Explicit observation interpretation |

## Goal

Add explicit `payload_summarize` and `payload_qa` tools so the agent can interpret long payloads intentionally, without Runtime auto-summary or hidden prompt injection.

## Current-State Analysis

`payload_read` and `payload_search` are live and deterministic. The architecture document still lists `payload_summarize` and `payload_qa` as future interpretation tools. No active schema/executor/API exists for them.

## Small Tickets

- [x] PR-170A — Common schemas and product semantics for `payload_summarize` / `payload_qa`.
- [x] PR-170B — Cortex interpretation endpoints and payload resolver budget/redaction.
- PR-170C — Runtime executors wired to Cortex interpretation endpoints.
- PR-170D — LLM Factory-backed implementation and monitor/Cortex observation tests.

## Done Criteria

- Summarize/QA only happen on explicit tool calls.
- Interpretation results become new Cortex observations.
- Raw payload remains behind ref.
- Failure semantics are visible and bounded.
