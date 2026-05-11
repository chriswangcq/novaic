# P003: Audit shell capability and tool CLI migration

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Find any remaining tool/harness surfaces that should now be shell CLI based but are still exposed or wired through old direct tools, missing agent identity binding, missing subagent binding, missing internal auth, or non-CLI paths.

## Success Criteria
- Inspect tool schema generation, shell capability scripts, runtime tool handlers, and monitor/desc wiring.
- Verify shell execution has explicit capability env and generated CLIs.
- Identify direct legacy harness tools that remain live without clear reason.
- Record evidence and any follow-up fixes.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
