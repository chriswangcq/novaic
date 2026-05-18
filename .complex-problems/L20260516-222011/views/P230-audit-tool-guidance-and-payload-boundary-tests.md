# P230: Audit tool guidance and payload boundary tests

Status: done
Parent: P129
Root: P000
Source Ticket: T220 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P230
Body: problems/P000/children/P003/children/P129/children/P230/README.md
Ticket(s): T231

## Problem
Agents need schema/guidance and tests that make payload inspection explicit rather than expecting large data inline in history.

## Success Criteria
- Tool schemas or docs for payload inspection expose explicit pointer-based operations.
- Existing tests cover payload refs and bounded read/search behavior, or gaps are identified.
- Any missing high-value test becomes follow-up work.

## Subproblems
- P239: Audit LLM tool schema and policy payload boundary
- P240: Audit shell capability guidance for payload and output boundaries

## Results
- R237

## Latest Check
C252

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P230/README.md
- Ticket T231: problems/P000/children/P003/children/P129/children/P230/tickets/T231.md
- Result R237: problems/P000/children/P003/children/P129/children/P230/results/R237.md
- Check C252: problems/P000/children/P003/children/P129/children/P230/checks/C252.md

## Follow-ups
- none
