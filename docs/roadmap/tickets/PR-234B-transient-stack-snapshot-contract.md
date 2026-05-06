# PR-234B — Transient Stack Snapshot Assembly Contract

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Parent | PR-234 |
| Scope | `novaic-common`, `novaic-agent-runtime/common` |

## Current State

Common LLM assembly appends the Active skill stack as an ordinary system message. If such a snapshot is ever persisted or replayed, it can compete with the fresh authoritative stack appended in a later round.

## Objective

Mark stack snapshots as transient control-plane guidance and filter old persisted stack snapshots before appending the fresh one.

## Small Tickets

- `[x]` Add a helper that builds the Active skill stack system message with transient metadata.
- `[x]` Filter prior messages that already look like Active skill stack snapshots.
- `[x]` Keep `format_active_skill_stack_message()` stable for callers that only need text.
- `[x]` Mirror the contract in `novaic-agent-runtime/common` if that local copy is still used.
- `[x]` Add Common assembly tests for metadata and stale snapshot filtering.

## Acceptance Criteria

- Exactly one fresh Active skill stack snapshot appears in an assembled LLM request.
- The snapshot is identifiable as transient metadata.
- Unit tests use only explicit assembly input values.

## Verification

- `cd novaic-common && pytest tests/test_llm_assembly_contract.py`
- `cd novaic-agent-runtime && pytest tests/test_pr85_llm_context_smoke_guardrails.py`
