# P048: Preserve Entangled row output shape under Postgres query paths

Status: done
Parent: P044
Root: P000
Source Ticket: T040 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P048
Body: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P048/README.md
Ticket(s): T043

## Problem
After query generation becomes dialect-aware, verify the client-visible row shapes are preserved for JSON, BOOL, TIMESTAMP-like fields, hidden fields, `has_<hidden>` markers, and list/list_stream responses.

## Success Criteria
- JSON input/output stays dict/list/scalar compatible.
- BOOL output stays Python bool-compatible.
- TIMESTAMP-like values remain string-compatible for first cutover.
- Hidden fields are removed and `has_<hidden>` markers remain correct.
- Existing SQLite behavior remains passing.
- Fake Postgres row-shape tests cover representative outputs without requiring a production Postgres instance.

## Subproblems
- none

## Results
- R039

## Latest Check
C040

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P048/README.md
- Ticket T043: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P048/tickets/T043.md
- Result R039: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P048/results/R039.md
- Check C040: problems/P000/children/P024/children/P027/children/P039/children/P044/children/P048/checks/C040.md

## Follow-ups
- none
