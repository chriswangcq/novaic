# P141: Workspace payload store and blob externalization map

Status: done
Parent: P134
Root: P000
Source Ticket: T127 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P141
Body: problems/P000/children/P003/children/P126/children/P134/children/P141/README.md
Ticket(s): T128

## Problem
Workspace payload write/read is the durable retrieval path for large tool outputs. It must keep full payloads out of normal context while preserving explicit readback through payload references.

## Success Criteria
- `write_payload` and `read_payload` behavior is mapped with source pointers.
- Local JSON versus external blob records are classified and tested.
- Payload manifests are verified to include source ref, stable step ref, size, hash, status, and retention class.
- Missing/corrupt/mismatch/blob-failure read paths are tested or split for follow-up.

## Subproblems
- none

## Results
- R124

## Latest Check
C138

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P141/README.md
- Ticket T128: problems/P000/children/P003/children/P126/children/P134/children/P141/tickets/T128.md
- Result R124: problems/P000/children/P003/children/P126/children/P134/children/P141/results/R124.md
- Check C138: problems/P000/children/P003/children/P126/children/P134/children/P141/checks/C138.md

## Follow-ups
- none
