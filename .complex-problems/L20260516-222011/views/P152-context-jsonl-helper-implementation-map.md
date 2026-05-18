# P152: context.jsonl helper implementation map

Status: done
Parent: P143
Root: P000
Source Ticket: T137 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P152
Body: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P152/README.md
Ticket(s): T138

## Problem
The workspace helper methods for `context.jsonl` must be mapped and classified at implementation level: whether they append raw messages, projections, or compatibility data, and whether any helper behavior can carry large payloads.

This belongs under `P143` because caller analysis is unsafe without first knowing exactly what each helper does.

## Success Criteria
- `read_context`, `append_context`, `append_context_projection`, `append_context_batch`, and `append_context_batch_projection` are mapped with source pointers.
- Each helper is classified by role and write/read behavior.
- Any helper behavior that can persist full raw payloads is identified or ruled out.

## Subproblems
- none

## Results
- R133

## Latest Check
C147

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P152/README.md
- Ticket T138: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P152/tickets/T138.md
- Result R133: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P152/results/R133.md
- Check C147: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P152/checks/C147.md

## Follow-ups
- none
