# Ticket: Narrow runtime bridge materialized context helper names

## Problem Definition

`CortexBridge.read_context`, `append_context`, and `append_context_batch` are projection-only helpers, but their names are broad enough to be mistaken for authoritative LLM context/history APIs.

## Proposed Solution

- Rename runtime bridge helpers to explicit materialized projection names.
- Update runtime callers and tests.
- Keep the HTTP endpoint behavior unchanged for this ticket.
- Add compatibility only if absolutely required by tests, but prefer physical cleanup of old helper names.

## Acceptance Criteria

- Production runtime code no longer calls `bridge.read_context`, `bridge.append_context`, or `bridge.append_context_batch`.
- Projection helper names include `materialized` or `projection`.
- LLM prepare code still calls `bridge.prepare_for_llm`.
- Focused runtime tests pass.

## Verification Plan

- Use `rg` to ensure old helper calls are gone from production runtime code.
- Run focused context read/append/session init/prepare tests.

## Risks

- Tests may still use old mocks; update tests to the new names instead of keeping broad compatibility aliases.

## Assumptions

- P445 may later adjust Cortex endpoint naming/docs; P443 only changes runtime bridge method names/callers.
