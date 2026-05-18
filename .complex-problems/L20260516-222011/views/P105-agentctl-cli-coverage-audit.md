# P105: Agentctl CLI Coverage Audit

Status: done
Parent: P103
Root: P000
Source Ticket: T098 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P105
Body: problems/P000/children/P002/children/P103/children/P105/README.md
Ticket(s): T099

## Problem
`agentctl` is the shell-first interface for IM, subagent, and agent/runtime-facing actions that used to be direct harness tools. It must be registered, discoverable, and covered by tests so agents can perform these actions through shell without hidden direct-tool assumptions.

## Success Criteria
- Locate `agentctl` implementation and command registration/help surfaces.
- Verify intended IM/subagent/media/payload-adjacent commands are reachable through shell docs or schema.
- Run focused tests or cheap local help checks for `agentctl` command availability.
- Fix misleading or missing coverage if found, or record a precise blocker/follow-up.

## Subproblems
- P108: Agentctl IM CLI Contract Audit
- P109: Agentctl Subagent CLI Contract Audit
- P110: Agentctl Media Audio-QA CLI Contract Audit

## Results
- R099

## Latest Check
C113

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P105/README.md
- Ticket T099: problems/P000/children/P002/children/P103/children/P105/tickets/T099.md
- Result R099: problems/P000/children/P002/children/P103/children/P105/results/R099.md
- Check C113: problems/P000/children/P002/children/P103/children/P105/checks/C113.md

## Follow-ups
- none
