# P108: Agentctl IM CLI Contract Audit

Status: done
Parent: P105
Root: P000
Source Ticket: T099 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P105/children/P108
Body: problems/P000/children/P002/children/P103/children/P105/children/P108/README.md
Ticket(s): T100

## Problem
Agent-facing IM read/reply/history/search operations should be reachable through `agentctl im ...` from shell and documented in the shell tool surface.

## Success Criteria
- Locate `agentctl im` implementation and command registration.
- Verify read/reply/history/search commands or their intended equivalents exist.
- Verify shell tool schema/docs mention the IM commands agents should use.
- Run focused tests or safe help checks; fix bounded gaps found.

## Subproblems
- none

## Results
- R096

## Latest Check
C110

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P105/children/P108/README.md
- Ticket T100: problems/P000/children/P002/children/P103/children/P105/children/P108/tickets/T100.md
- Result R096: problems/P000/children/P002/children/P103/children/P105/children/P108/results/R096.md
- Check C110: problems/P000/children/P002/children/P103/children/P105/children/P108/checks/C110.md

## Follow-ups
- none
