# P033: Tighten LogicalFS Boundary Guardrails

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P019/children/P024/children/P033
Body: problems/P000/children/P019/children/P024/children/P033/README.md
Ticket(s): T033

## Problem
`tests/blob_boundary_policy.py` still has transitional allowlist entries for old Cortex authority files, `BlobCortexStore`, and `/v1/objects` usage that should now live only in LogicalFS/Blob infrastructure.

## Success Criteria
- Guardrail policy no longer allows `novaic_cortex/workspace_files.py` or `BlobCortexStore`.
- Guardrail policy permits `/v1/objects` only in the LogicalFS Blob object adapter and Blob service/docs where appropriate, not Cortex runtime.
- Guardrail tests pass and fail the old direct-Cortex live file patterns.

## Subproblems
- none

## Results
- R031

## Latest Check
C031

## Bodies
- Problem: problems/P000/children/P019/children/P024/children/P033/README.md
- Ticket T033: problems/P000/children/P019/children/P024/children/P033/tickets/T033.md
- Result R031: problems/P000/children/P019/children/P024/children/P033/results/R031.md
- Check C031: problems/P000/children/P019/children/P024/children/P033/checks/C031.md

## Follow-ups
- none
