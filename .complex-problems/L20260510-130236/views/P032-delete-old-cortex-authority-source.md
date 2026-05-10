# P032: Delete Old Cortex Authority Source

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P019/children/P024/children/P032
Body: problems/P000/children/P019/children/P024/children/P032/README.md
Ticket(s): T032

## Problem
`novaic-cortex/novaic_cortex/workspace_files.py` still contains `CortexLogicalFileAuthority`, and nearby source/docs in `store.py` still describe the old in-process authority. Even if not imported by active runtime, this production source residue can be revived by future edits.

## Success Criteria
- `workspace_files.py` is deleted or replaced with a non-production/test-only alternative.
- Production source has no `CortexLogicalFileAuthority` or `BlobCortexStore` definitions/imports.
- `store.py` wording no longer claims it is below `CortexLogicalFileAuthority`.
- Source-level residue scan passes for old authority names outside explicitly historical docs/tests.

## Subproblems
- none

## Results
- R030

## Latest Check
C030

## Bodies
- Problem: problems/P000/children/P019/children/P024/children/P032/README.md
- Ticket T032: problems/P000/children/P019/children/P024/children/P032/tickets/T032.md
- Result R030: problems/P000/children/P019/children/P024/children/P032/results/R030.md
- Check C030: problems/P000/children/P019/children/P024/children/P032/checks/C030.md

## Follow-ups
- none
