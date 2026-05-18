# Ticket: Display Perception Cleanup And Regression Audit

## Summary

Run the display perception cleanup pass: remove stale durable-base64 assumptions, execute focused regression tests, and record remaining unrelated failures explicitly.

## Problem Definition

Runtime/Cortex/resolver implementation is now changed, but old tests and helper paths can still encode the previous base64-in-durable-payload contract. This ticket checks and cleans the display perception surface so the active code does not silently retain the old behavior.

## Proposed Solution

Search runtime and Cortex for durable display base64 expectations, run focused display-related tests across runtime and Cortex, and repair any display-contract failures. Keep unrelated pre-existing failures documented rather than hiding them.

## Acceptance Criteria

- No active display durable-payload code or focused tests expect persisted `_mcp_content[].data`.
- Runtime display handler, Cortex projection, runtime resolver, and historical image-injection tests pass.
- Searches distinguish valid provider/request image base64 from invalid durable/history base64.
- Any unrelated failures are recorded with clear boundaries.

## Verification Plan

Run focused pytest commands and targeted `rg` searches for:

- `durable_payload`,
- `image_ref`,
- `_mcp_content` + `data`,
- `display_perception`,
- `YWJjMTIz` fixture residues.
