# Audit runtime prepare-context handler chain

## Problem Definition

The runtime decides when to call Cortex `prepare_for_llm`, how that response flows through queue saga steps, and how the final LLM handler receives messages/tools. This chain must be mapped precisely so live provider calls use the ContextEvent-backed snapshot rather than stale local continuity or old `context.read` projections.

## Proposed Solution

Inspect the runtime prepare-context path across `cortex_handlers.py`, `runtime_handlers.py`, `context_handlers.py`, `react_think.py`, and the `react_think` contracts. Map the saga step ordering, the Cortex prepare response shape, the handoff into `llm.call`, and any local continuity/context-read side paths. Classify each side path as active-safe, dead, or stale. Add or update focused runtime tests/static guards if mapping reveals a missing assumption guard.

## Acceptance Criteria

- Source pointers map prepare-context related code in `cortex_handlers.py`, `runtime_handlers.py`, `context_handlers.py`, `react_think.py`, and `react_think` contracts.
- The handoff from queue saga step to Cortex prepare response to final LLM input is documented with exact data fields.
- Remaining local cross-wake continuity or `context.read` side paths are classified as active-safe, dead, or stale.
- Relevant runtime tests/static checks are identified and run.
- Any active stale continuity path that can affect provider messages is fixed or split into a blocking child problem.

## Verification Plan

- Search runtime code for `prepare_context`, `prepare_for_llm`, `read_context`, `context.read`, `continuity`, and `build_llm_call_payload`.
- Inspect source slices around the active saga and handlers.
- Run focused runtime tests such as `test_pr85_llm_context_smoke_guardrails.py`, `test_runtime_explicit_contracts.py`, `test_context_read_by_ids.py`, `test_context_read_ordering.py`, and any newly added guard tests.

## Risks

- Several paths may be active but safe for notification hinting or idempotency rather than LLM provider input; do not delete them without classification.
- If the handler chain is too broad for one bounded audit, split into saga ordering, handler response shape, and local continuity residue children.

## Assumptions

- Cortex `prepare_for_llm` is intended to be the authoritative LLM context source.
- Existing context-read side paths may remain valid only when they do not feed final provider messages.
