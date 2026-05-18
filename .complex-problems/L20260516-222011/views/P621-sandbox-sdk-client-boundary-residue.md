# P621: Sandbox SDK Client Boundary Residue

Status: done
Parent: P565
Root: P000
Source Ticket: T615 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565/children/P621
Body: problems/P000/children/P005/children/P553/children/P565/children/P621/README.md
Ticket(s): T617

## Problem
Audit `novaic-sandbox-sdk` and runtime call sites to confirm clients talk to sandboxd/service instead of direct legacy process execution or host path manipulation.

## Success Criteria
- Records exact scans for SDK client, exec/session API, base64 wire decoding, fallback/local paths, and runtime call sites.
- Cites SDK/runtime slices.
- Runs focused SDK tests and runtime shell output tests.
- Creates follow-up if active runtime bypasses sandboxd.

## Subproblems
- P623: Sandbox SDK API and Wire Boundary Residue
- P624: Runtime Sandbox SDK Call Site Residue
- P625: Sandbox SDK Runtime Boundary Test Coverage

## Results
- R618

## Latest Check
C659

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/children/P621/README.md
- Ticket T617: problems/P000/children/P005/children/P553/children/P565/children/P621/tickets/T617.md
- Result R618: problems/P000/children/P005/children/P553/children/P565/children/P621/results/R618.md
- Check C659: problems/P000/children/P005/children/P553/children/P565/children/P621/checks/C659.md

## Follow-ups
- none
