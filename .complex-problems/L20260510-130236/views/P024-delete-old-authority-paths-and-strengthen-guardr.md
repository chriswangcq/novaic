# P024: Delete Old Authority Paths And Strengthen Guardrails

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P019/children/P024
Body: problems/P000/children/P019/children/P024/README.md
Ticket(s): T031

## Problem
After cutover, old authority code, compatibility constructors, stale docs, or broad allowlists can keep the system ambiguous and make future agents accidentally revive dead paths. This belongs under T019 because the user explicitly wants no half-migration and no legacy branch kept for compatibility.

## Success Criteria
- Old Cortex-owned live file authority code is physically deleted or moved to clearly test-only support with no production imports.
- Guardrail tests fail direct live Workspace usage of `CortexStore`, `BlobCortexStore`, `/v1/objects`, or old backing sandbox paths outside approved LogicalFS internals.
- Docs describe the final module relationship: Cortex semantic layer, LogicalFS realtime `RO` / `RW`, sandboxd process execution, Blob cheap bytes.
- Stale wording that implies Blob/Cortex owns live workspace files is removed.
- Canonical backend tests and targeted residue scans pass.

## Subproblems
- P032: Delete Old Cortex Authority Source
- P033: Tighten LogicalFS Boundary Guardrails
- P034: Rewrite Final LogicalFS Architecture Docs
- P035: Final Old Authority Cleanup Verification

## Results
- R034

## Latest Check
C034

## Bodies
- Problem: problems/P000/children/P019/children/P024/README.md
- Ticket T031: problems/P000/children/P019/children/P024/tickets/T031.md
- Result R034: problems/P000/children/P019/children/P024/results/R034.md
- Check C034: problems/P000/children/P019/children/P024/checks/C034.md

## Follow-ups
- none
