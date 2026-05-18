# P600: Factory Log Request Context and Raw JSON Boundary

Status: done
Parent: P583
Root: P000
Source Ticket: T592 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P600
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P600/README.md
Ticket(s): T593

## Problem
Audit factory-log storage/API and raw JSON detail paths to ensure they represent actual LLM request context, not monitor previews, and do not store unredacted display raw media bytes outside the intended provider request.

## Success Criteria
- Records exact scans for factory-log APIs, request/response body persistence, and raw JSON rendering data.
- Cites backend slices that show what is stored for LLM calls.
- Cites frontend slices that show raw JSON detail is a human debug view of stored call records.
- Creates a follow-up if raw media bytes are stored in factory logs unexpectedly.

## Subproblems
- none

## Results
- R587

## Latest Check
C625

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P600/README.md
- Ticket T593: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P600/tickets/T593.md
- Result R587: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P600/results/R587.md
- Check C625: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P600/checks/C625.md

## Follow-ups
- none
