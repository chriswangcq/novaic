# P145: normalize_step observation contract audit

Status: done
Parent: P142
Root: P000
Source Ticket: T129 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P145
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P145/README.md
Ticket(s): T130

## Problem
`normalize_step` is the first gate before tool results become workspace step files. It must reject legacy inline raw `result` fields and require a structured observation/percept shape so raw CLI output, base64, or large JSON cannot sneak into `steps/*.json` as the canonical result.

This child belongs under `P142` because step indexing can only be trusted if the normalized step object has already removed unsafe legacy result fields.

## Success Criteria
- Source pointers map the `normalize_step` implementation and its validation branches.
- Tests or direct evidence prove inline `result` input is rejected for new step writes.
- Tests or direct evidence prove missing/invalid observation input is rejected.
- Residual historical compatibility, if any, is explicitly scoped away from new write paths.

## Subproblems
- none

## Results
- R125

## Latest Check
C139

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P145/README.md
- Ticket T130: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P145/tickets/T130.md
- Result R125: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P145/results/R125.md
- Check C139: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P145/checks/C139.md

## Follow-ups
- none
