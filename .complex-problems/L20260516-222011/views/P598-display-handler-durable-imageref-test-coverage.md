# P598: Display Handler Durable ImageRef Test Coverage

Status: done
Parent: P595
Root: P000
Source Ticket: T587 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P598
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P598/README.md
Ticket(s): T589

## Problem
Verify the runtime display handler durable payload is protected by tests that store BlobRef `image_ref` metadata and omit inline image `data`.

## Success Criteria
- Records exact scans for display handler durable payload tests.
- Cites tests proving display public output replaces images with placeholders and durable payload stores `image_ref`.
- Cites tests proving durable payload does not depend on inline base64 data.
- Creates a concrete follow-up if display durable coverage is missing.

## Subproblems
- none

## Results
- R582

## Latest Check
C620

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P598/README.md
- Ticket T589: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P598/tickets/T589.md
- Result R582: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P598/results/R582.md
- Check C620: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P598/checks/C620.md

## Follow-ups
- none
