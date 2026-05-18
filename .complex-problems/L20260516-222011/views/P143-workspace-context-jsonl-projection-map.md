# P143: Workspace context.jsonl projection map

Status: done
Parent: P134
Root: P000
Source Ticket: T127 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P143
Body: problems/P000/children/P003/children/P126/children/P134/children/P143/README.md
Ticket(s): T137

## Problem
`context.jsonl` helpers still append and read materialized message projections. Their role must be classified precisely so they do not get mistaken for the authoritative LLM context source.

## Success Criteria
- `read_context`, `append_context`, `append_context_projection`, `append_context_batch`, and `append_context_batch_projection` are mapped with source pointers.
- Consumers/callers of these helpers are identified.
- The helpers are classified as materialized/debug projection, compatibility path, active source, or stale.
- If any active LLM prepare path reads `context.jsonl` as authority, it is fixed or split.
- Tests covering context write projections are identified and run.

## Subproblems
- P152: context.jsonl helper implementation map
- P153: context.jsonl caller classification
- P154: LLM prepare path context authority audit
- P155: context projection regression test audit

## Results
- R140

## Latest Check
C154

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P143/README.md
- Ticket T137: problems/P000/children/P003/children/P126/children/P134/children/P143/tickets/T137.md
- Result R140: problems/P000/children/P003/children/P126/children/P134/children/P143/results/R140.md
- Check C154: problems/P000/children/P003/children/P126/children/P134/children/P143/checks/C154.md

## Follow-ups
- none
