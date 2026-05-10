# P007: Add Blob live RO/RW bypass guardrails

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P007
Body: problems/P000/children/P004/children/P007/README.md
Ticket(s): T006

## Problem
The repository needs tests or scripts that fail if new direct Blob/object calls
become live `RO` / `RW` file authorities outside the allowed boundary.

## Success Criteria
- Guardrails allow Blob payload/display/audio/attachment byte use.
- Guardrails allow transitional persistence adapter internals only in explicitly
- named files.
- Guardrails fail obvious direct `/v1/objects` or `BlobCortexStore` usage from
- Workspace/API/runtime/sandbox code.
- Guardrails are part of targeted tests or CI scripts.

## Subproblems
- P010: Define Blob Boundary Guardrail Allowlist
- P011: Implement Blob Boundary Guardrail Test
- P012: Prove Blob Boundary Guardrail Behavior

## Results
- R007

## Latest Check
C007

## Bodies
- Problem: problems/P000/children/P004/children/P007/README.md
- Ticket T006: problems/P000/children/P004/children/P007/tickets/T006.md
- Result R007: problems/P000/children/P004/children/P007/results/R007.md
- Check C007: problems/P000/children/P004/children/P007/checks/C007.md

## Follow-ups
- none
