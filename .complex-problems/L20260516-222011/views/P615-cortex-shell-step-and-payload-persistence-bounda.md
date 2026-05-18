# P615: Cortex Shell Step and Payload Persistence Boundary

Status: done
Parent: P576
Root: P000
Source Ticket: T607 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P615
Body: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P615/README.md
Ticket(s): T609

## Problem
Audit Cortex step/payload recording for shell results to confirm full details are recoverable through RO/payload references while normal LLM history uses bounded previews.

## Success Criteria
- Records scans for Cortex step write, payload ref, preview/head/tail, and RO step persistence logic.
- Cites code/test slices proving full output is stored outside normal history text when needed.
- Classifies payload refs and full-output files as intended or risky.
- Creates follow-up if durable shell history stores raw media bytes inline.

## Subproblems
- none

## Results
- R604

## Latest Check
C645

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P615/README.md
- Ticket T609: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P615/tickets/T609.md
- Result R604: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P615/results/R604.md
- Check C645: problems/P000/children/P005/children/P553/children/P564/children/P576/children/P615/checks/C645.md

## Follow-ups
- none
