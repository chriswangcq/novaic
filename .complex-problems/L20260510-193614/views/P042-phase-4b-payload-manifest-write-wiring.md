# P042: Phase 4B Payload Manifest Write Wiring

Status: done
Parent: P005
Root: P000
Package: problems/P000/children/P005/children/P042
Body: problems/P000/children/P005/children/P042/README.md
Ticket(s): T041

## Problem
Payload writes currently create scope-local `payloads/*.json` records and may externalize bytes to Blob, but semantic manifest rows are not guaranteed on the live path. The write path must record manifest state in operational SQLite/Workspace at the same semantic boundary where Cortex decides what the payload means.

## Success Criteria
- `Workspace.write_payload` records manifest rows for external Blob payloads with source ref, returned BlobRef, scope/root/step linkage, size/hash/type, status, retention class, and timestamps.
- Local JSON payloads either record manifest rows or have an explicit tested design decision for scope-local-only handling.
- Step normalization/indexing continues to use the final payload ref without duplicating raw payload bytes in step files.
- Tests cover large externalized payload manifest creation, local payload behavior, manifest lookup, and retention markers.

## Subproblems
- none

## Results
- R039

## Latest Check
C042

## Bodies
- Problem: problems/P000/children/P005/children/P042/README.md
- Ticket T041: problems/P000/children/P005/children/P042/tickets/T041.md
- Result R039: problems/P000/children/P005/children/P042/results/R039.md
- Check C042: problems/P000/children/P005/children/P042/checks/C042.md

## Follow-ups
- none
