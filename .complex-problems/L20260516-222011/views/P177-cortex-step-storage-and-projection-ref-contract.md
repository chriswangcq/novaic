# P177: Cortex step storage and projection ref contract

Status: done
Parent: P136
Root: P000
Source Ticket: T164 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P136/children/P177
Body: problems/P000/children/P003/children/P126/children/P136/children/P177/README.md
Ticket(s): T166

## Problem
Cortex workspace step writes and context projections persist tool results for later lookup. This layer must keep `step_ref` stable for step lookup and preserve actual/externalized `payload_ref` metadata without corrupt JSONL, hidden fallback, or ambiguous index entries.

## Success Criteria
- Map Cortex `write_step`, step index, context projection, and step read code around `step_ref`, `payload_ref`, and artifacts.
- Document how step index entries should represent stable step identity versus actual payload storage.
- Run focused Cortex tests for step index, context writes, corrupt JSONL fail-closed behavior, and artifact metadata.
- Fix or split any ambiguous duplicate-key behavior.

## Subproblems
- none

## Results
- R162

## Latest Check
C176

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P136/children/P177/README.md
- Ticket T166: problems/P000/children/P003/children/P126/children/P136/children/P177/tickets/T166.md
- Result R162: problems/P000/children/P003/children/P126/children/P136/children/P177/results/R162.md
- Check C176: problems/P000/children/P003/children/P126/children/P136/children/P177/checks/C176.md

## Follow-ups
- none
