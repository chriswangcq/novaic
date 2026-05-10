# P043: Phase 4C Payload Read And Failure Semantics

Status: done
Parent: P005
Root: P000
Package: problems/P000/children/P005/children/P043
Body: problems/P000/children/P005/children/P043/README.md
Ticket(s): T042

## Problem
`Workspace.read_payload` and Blob fetch failures need explicit semantic behavior. Missing scope-local payload records, payload_ref mismatch, missing Blob client, Blob fetch failure, malformed JSON, and missing blob should update/report manifest status predictably instead of surfacing accidental low-level exceptions as the only truth.

## Success Criteria
- `read_payload` consults manifest state where needed and returns explicit domain errors for missing/corrupt/unavailable payloads.
- Blob fetch/missing/corrupt failures update manifest status with structured error information.
- Payload ref mismatch and malformed scope-local records are explicit, tested failures.
- Tests cover missing blob/fetch failure, malformed local record, payload_ref mismatch, and successful manifest-backed read.

## Subproblems
- none

## Results
- R040

## Latest Check
C043

## Bodies
- Problem: problems/P000/children/P005/children/P043/README.md
- Ticket T042: problems/P000/children/P005/children/P043/tickets/T042.md
- Result R040: problems/P000/children/P005/children/P043/results/R040.md
- Check C043: problems/P000/children/P005/children/P043/checks/C043.md

## Follow-ups
- none
