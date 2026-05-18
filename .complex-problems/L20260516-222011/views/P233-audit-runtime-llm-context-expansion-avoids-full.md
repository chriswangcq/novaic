# P233: Audit runtime LLM context expansion avoids full payload reads

Status: done
Parent: P229
Root: P000
Source Ticket: T222 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P233
Body: problems/P000/children/P003/children/P129/children/P229/children/P233/README.md
Ticket(s): T229

## Problem
The normal runtime path that prepares LLM messages must not call full payload read APIs or inline durable payload bodies by default. It should request compact formatted step projections/previews for historical tool results.

This belongs under `P229` because runtime context preparation is the final boundary before data enters the model request.

## Success Criteria
- Runtime message expansion path is mapped with file/function pointers.
- Evidence shows default context preparation uses formatted projection APIs, not `/v1/payload/read` or equivalent full durable payload reads.
- Focused runtime tests verify historical shell/display outputs remain compact in LLM request messages.

## Subproblems
- none

## Results
- R225

## Latest Check
C239

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P233/README.md
- Ticket T229: problems/P000/children/P003/children/P129/children/P229/children/P233/tickets/T229.md
- Result R225: problems/P000/children/P003/children/P129/children/P229/children/P233/results/R225.md
- Check C239: problems/P000/children/P003/children/P129/children/P229/children/P233/checks/C239.md

## Follow-ups
- none
