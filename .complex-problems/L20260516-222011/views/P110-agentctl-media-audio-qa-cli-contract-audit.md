# P110: Agentctl Media Audio-QA CLI Contract Audit

Status: done
Parent: P105
Root: P000
Source Ticket: T099 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P105/children/P110
Body: problems/P000/children/P002/children/P103/children/P105/children/P110/README.md
Ticket(s): T102

## Problem
Audio/media helper actions migrated behind shell should be reachable through `agentctl media audio-qa` and should not rely on stale direct tool exposure for normal agent behavior.

## Success Criteria
- Locate `agentctl media audio-qa` implementation and registration.
- Verify shell tool schema/docs mention the command.
- Verify output remains text/artifact-contract compatible and does not introduce hidden binary/base64 LLM payloads.
- Run focused tests or safe help checks; fix bounded gaps found.

## Subproblems
- none

## Results
- R098

## Latest Check
C112

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P105/children/P110/README.md
- Ticket T102: problems/P000/children/P002/children/P103/children/P105/children/P110/tickets/T102.md
- Result R098: problems/P000/children/P002/children/P103/children/P105/children/P110/results/R098.md
- Check C112: problems/P000/children/P002/children/P103/children/P105/children/P110/checks/C112.md

## Follow-ups
- none
