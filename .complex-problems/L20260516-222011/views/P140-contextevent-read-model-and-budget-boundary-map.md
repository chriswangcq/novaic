# P140: ContextEvent read model and budget boundary map

Status: done
Parent: P133
Root: P000
Source Ticket: T123 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P133/children/P140
Body: problems/P000/children/P003/children/P126/children/P133/children/P140/README.md
Ticket(s): T126

## Problem
`ContextEventReadModel.prepare` turns pure projection output into prepared LLM context with budget compaction and top-first stack normalization. That boundary must be verified separately from raw event projection.

## Success Criteria
- Read-model behavior for empty roots, projection, budget compaction, token counting, usage ratio, and top-first stack normalization is documented.
- Read-model tests are identified and run.
- Any implicit fallback to old context assembly is classified and fixed or split.

## Subproblems
- none

## Results
- R122

## Latest Check
C136

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P133/children/P140/README.md
- Ticket T126: problems/P000/children/P003/children/P126/children/P133/children/P140/tickets/T126.md
- Result R122: problems/P000/children/P003/children/P126/children/P133/children/P140/results/R122.md
- Check C136: problems/P000/children/P003/children/P126/children/P133/children/P140/checks/C136.md

## Follow-ups
- none
