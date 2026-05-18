# Runtime projection inventory ticket

## Problem Definition

Runtime is the boundary that turns Cortex step projections and shell results into the next LLM request. It must only inject image media for explicit current display perception, keep shell output terminal-like, and keep historical/generic tool outputs text-only.

## Proposed Solution

Inspect runtime projection/message code and classify suspicious branches with line evidence. Do not edit code.

## Acceptance Criteria

- Covers step projection selection, `_projection` handling, image placeholder sanitization, generic/historical tool image rejection, explicit display perception injection, shell output truncation, and shell CLI artifact manifest handling.
- Classifies suspicious branches and cleanup candidates.
- No code changes.

## Verification Plan

Use `rg` and `nl` over runtime task queue modules and tests as evidence.

## Risks

- Runtime may intentionally keep a defensive guard against old tool payloads; classification should preserve it only if it prevents leakage.

## Assumptions

- This ticket is read-only inventory.
