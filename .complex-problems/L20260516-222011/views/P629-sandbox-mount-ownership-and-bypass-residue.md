# P629: Sandbox Mount Ownership and Bypass Residue

Status: done
Parent: P622
Root: P000
Source Ticket: T623 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P629
Body: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P629/README.md
Ticket(s): T625

## Problem
Classify mount/source_root/stable_cwd handling across SDK DTOs, Cortex LogicalFS planning, and sandbox-service mount namespace internals to confirm mount ownership is layered and clients cannot bypass sandboxd.

## Success Criteria
- Records exact scans for mount/source_root/stable_cwd/bind/namespace/host path terms.
- Cites SDK DTO, Cortex LogicalFS mount plan, and sandbox-service mount namespace slices.
- Classifies each hit as DTO, Cortex planning, service-internal, test fixture, or risky bypass.
- Runs focused sandboxd/logicalfs/mount tests.
- Creates follow-up if client-side mount bypass remains.

## Subproblems
- none

## Results
- R620

## Latest Check
C661

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P629/README.md
- Ticket T625: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P629/tickets/T625.md
- Result R620: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P629/results/R620.md
- Check C661: problems/P000/children/P005/children/P553/children/P565/children/P622/children/P629/checks/C661.md

## Follow-ups
- none
