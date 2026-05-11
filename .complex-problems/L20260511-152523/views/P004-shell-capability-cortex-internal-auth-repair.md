# P004: Shell capability Cortex internal auth repair

Status: done
Parent: P002
Root: P000
Package: problems/P000/children/P002/children/P004
Body: problems/P000/children/P002/children/P004/README.md
Ticket(s): T003

## Problem
Runtime-injected shell capability commands such as `agentctl im read` call Cortex internal endpoints, but the capability script does not attach `X-Internal-Key`, and runtime does not pass the Cortex internal key into the shell capability environment. This causes deterministic 401 failures from Cortex `/v1/meta/read`.

## Success Criteria
- Runtime shell execution passes `NOVAIC_CORTEX_INTERNAL_KEY` through the explicit capability env when configured.
- Cortex shell capability scripts allow that env key and use it only for Cortex internal requests.
- Regression tests prove `agentctl`/Cortex capability requests carry `X-Internal-Key` without leaking into unrelated business/device calls.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/children/P004/README.md
- Ticket T003: problems/P000/children/P002/children/P004/tickets/T003.md
- Result R001: problems/P000/children/P002/children/P004/results/R001.md
- Check C001: problems/P000/children/P002/children/P004/checks/C001.md

## Follow-ups
- none
