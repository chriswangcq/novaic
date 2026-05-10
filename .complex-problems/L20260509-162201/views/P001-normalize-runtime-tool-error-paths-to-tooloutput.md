# P001: Normalize Runtime tool error paths to ToolOutputV1

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Runtime `_ok()` now normalizes successful executor returns to `ToolOutputV1`, but `_err()` still stores raw legacy JSON for unknown tool names and handler exceptions. This leaves one durable tool-result path outside the new contract.

## Success Criteria
- `_err()` stores `content` as `ToolOutputV1` JSON with `ok=false`.
- Unknown-tool and exception paths preserve current task status/error semantics.
- Tests assert the failure-path envelope has `version == "tool-output.v1"` and includes the error text.
- Focused Runtime tool handler failure tests pass.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R001: problems/P000/children/P001/results/R001.md
- Check C001: problems/P000/children/P001/checks/C001.md

## Follow-ups
- none
