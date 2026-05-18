# Ticket: Inventory runtime bridge endpoint usage

## Problem Definition

The runtime bridge surface must be mapped before cleanup. The repo may still have context projection, payload, and tool-result endpoint calls through direct URLs or helper names.

## Proposed Solution

- Run targeted searches across runtime, Cortex, tests, and frontend/backend service code for context/payload/tool-result bridge endpoints and helper names.
- Save caller inventories and representative source slices.
- Classify each hit by owner: live agent loop, notification injection, debug/inspection, bounded payload inspection, test-only, or unresolved.

## Acceptance Criteria

- Inventory artifacts cover `/v1/context/*`, `/v1/payload/*`, `/v1/tool-result/*`, `read_context`, `append_context`, `batch_context`, `prepare_for_llm`, and projection helper names.
- Representative live code slices are saved.
- All hits are classified; unresolved hits are explicitly listed for P438/P439.
- No implementation change is made in this inventory ticket.

## Verification Plan

- Use `rg` scans with generated ledger artifacts excluded.
- Save source slices for bridge helpers and runtime handlers.
- Validate classification by spot-checking each live category.

## Risks

- Endpoint names can appear in tests and docs. Do not treat all textual hits as live code.

## Assumptions

- This ticket is evidence-only; cleanup occurs in later child problems.
