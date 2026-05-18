# P597: Shell Screenshot CLI BlobRef Manifest Test Coverage

Status: done
Parent: P595
Root: P000
Source Ticket: T587 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P597
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P597/README.md
Ticket(s): T588

## Problem
Verify shell-facing screenshot/device CLI output is protected by tests that require BlobRef artifact manifests instead of raw base64 terminal text.

## Success Criteria
- Records exact scans for shell/devicectl screenshot BlobRef manifest tests.
- Cites tests proving shell screenshot output contains `tool-output.v1` artifact metadata and BlobRef access instructions.
- Cites tests proving raw screenshot base64 is absent from shell-visible/durable text.
- Creates a concrete follow-up if shell CLI manifest coverage is missing.

## Subproblems
- none

## Results
- R581

## Latest Check
C619

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P597/README.md
- Ticket T588: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P597/tickets/T588.md
- Result R581: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P597/results/R581.md
- Check C619: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/children/P595/children/P597/checks/C619.md

## Follow-ups
- none
