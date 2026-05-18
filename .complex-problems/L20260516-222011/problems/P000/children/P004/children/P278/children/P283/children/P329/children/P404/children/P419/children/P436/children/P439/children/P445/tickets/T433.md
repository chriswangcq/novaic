# Ticket: Clean Cortex materialized context endpoint and test wording

## Problem Definition

Cortex `/v1/context/read|append|batch` endpoints and tests still use broad context wording. Since LLM prepare now uses ContextEvent read model, these endpoints/tests should clearly describe materialized projection behavior.

## Proposed Solution

- Update Cortex endpoint comments/docstrings where they imply generic context or LLM history.
- Update relevant tests to name/read as materialized projection tests.
- Keep endpoint paths and behavior unchanged.
- Run Cortex context event API and prepare-path guard tests.

## Acceptance Criteria

- Cortex endpoint docs/comments call these materialized projection APIs.
- Tests that read `ws.read_context` are clearly projection tests.
- Prepare-path guard tests still prove no `read_context` fallback.
- Focused Cortex tests pass.

## Verification Plan

- Patch wording in `novaic_cortex/api.py` and relevant tests if needed.
- Run focused Cortex context write/read and prepare guard suites.
- Run `rg` scan for misleading broad wording around `/v1/context/read|append|batch`.

## Risks

- Endpoint paths are public internal API names; do not rename paths in this ticket.

## Assumptions

- Runtime bridge/handler wording was handled in P443/P444.
