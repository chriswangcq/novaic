# Ticket: Classify materialized context projection owners

## Problem Definition

Materialized context projection endpoints and bridge helpers are live, but their owners must be classified before cleanup. Without classification, deleting or renaming could break notification delivery or tests.

## Proposed Solution

- Use P437 inventories plus fresh targeted scans.
- Save source slices for each live owner.
- Classify every `read_context`, `append_context`, `append_context_batch`, `/v1/context/read`, `/v1/context/append`, and `/v1/context/batch` hit.

## Acceptance Criteria

- Classification artifact lists every live hit and owner.
- Unresolved or misleading owner names are routed to P443/P444/P445.
- No code changes are made.

## Verification Plan

- Run `rg` over runtime/Cortex/tests excluding generated ledger.
- Spot-check source slices for runtime handlers, bridge helpers, and Cortex endpoints.

## Risks

- Tests and docs can look like live code; classify them separately.

## Assumptions

- P443/P444/P445 will make actual changes based on the classification.
