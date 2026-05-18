# P170: LLM payload handoff regression coverage audit

Status: done
Parent: P161
Root: P000
Source Ticket: T153 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P170
Body: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P170/README.md
Ticket(s): T158

## Problem
Even if the current builder and handler look correct, regressions can reintroduce stale context handoff. The runtime test suite must contain a focused guard that would fail if prepare-context output stopped being the sole authority for provider messages/tools.

## Success Criteria
- Existing tests covering prepare-result-to-LLM handoff are identified with line pointers.
- Missing direct guards are added or a follow-up is split if coverage cannot be completed safely.
- The focused runtime test slice is run and reported.
- The check explicitly states what plausible regression the tests would catch.

## Subproblems
- none

## Results
- R153

## Latest Check
C167

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P170/README.md
- Ticket T158: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P170/tickets/T158.md
- Result R153: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P170/results/R153.md
- Check C167: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P170/checks/C167.md

## Follow-ups
- none
