# P109: Agentctl Subagent CLI Contract Audit

Status: done
Parent: P105
Root: P000
Source Ticket: T099 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P105/children/P109
Body: problems/P000/children/P002/children/P103/children/P105/children/P109/README.md
Ticket(s): T101

## Problem
Subagent spawning/coordination should be reachable through `agentctl subagent ...` from shell so direct harness subagent tools are not required for normal agent work.

## Success Criteria
- Locate `agentctl subagent` implementation and command registration.
- Verify spawn and message/coordination command coverage matches the intended shell-first surface.
- Verify shell tool schema/docs mention the subagent commands agents should use.
- Run focused tests or safe help checks; fix bounded gaps found.

## Subproblems
- none

## Results
- R097

## Latest Check
C111

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P105/children/P109/README.md
- Ticket T101: problems/P000/children/P002/children/P103/children/P105/children/P109/tickets/T101.md
- Result R097: problems/P000/children/P002/children/P103/children/P105/children/P109/results/R097.md
- Check C111: problems/P000/children/P002/children/P103/children/P105/children/P109/checks/C111.md

## Follow-ups
- none
