# P229: Audit payload write and normal context assembly boundaries

Status: done
Parent: P129
Root: P000
Source Ticket: T220 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229
Body: problems/P000/children/P003/children/P129/children/P229/README.md
Ticket(s): T222

## Problem
Tool/step write paths should store large outputs by payload reference, while normal context assembly should use compact projections rather than full payload reads.

## Success Criteria
- Tool/step write path records `step_ref`/`payload_ref` evidence.
- Normal LLM context expansion path does not call full payload read by default.
- Large shell/display raw data stays behind durable payload or explicit payload APIs.

## Subproblems
- P231: Audit tool step write path durable payload refs
- P232: Audit Cortex event projection preserves payload pointers
- P233: Audit runtime LLM context expansion avoids full payload reads
- P234: Audit large shell/display output projection boundary

## Results
- R227

## Latest Check
C241

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/README.md
- Ticket T222: problems/P000/children/P003/children/P129/children/P229/tickets/T222.md
- Result R227: problems/P000/children/P003/children/P129/children/P229/results/R227.md
- Check C241: problems/P000/children/P003/children/P129/children/P229/checks/C241.md

## Follow-ups
- none
