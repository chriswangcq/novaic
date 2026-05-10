# Complex Problem Ledger

Ledger: L20260509-162201
Schema: v6
Root: P000 - Runtime ToolOutputV1 normalization
Status: done
Updated: 2026-05-09T08:28:16+00:00

## Problem Tree
- [done] P000: Runtime ToolOutputV1 normalization
  - [done] P001: Normalize Runtime tool error paths to ToolOutputV1

## Active

## Blocked

## Done
- [x] P000: Runtime ToolOutputV1 normalization
- [x] P001: Normalize Runtime tool error paths to ToolOutputV1

## Tickets
- [done] T000: Normalize Runtime tool success content to ToolOutputV1 -> P000 (one_go)
- [done] T001: Normalize `_err()` content to ToolOutputV1 -> P001 (one_go)

## Latest Checks
- [not_success] C000: P000 Success path emits ToolOutputV1 but failure path _err still uses a legacy raw error envelope
- [success] C001: P001 Runtime _err failure paths now emit ToolOutputV1 content and focused tests pass
- [success] C002: P000 Runtime tool success and failure paths now store ToolOutputV1 content; focused Runtime and Cortex tests pass
