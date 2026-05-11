# P001: Live production stall diagnosis

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Determine the exact production stuck state after one agent loop. Inspect live process status, runtime/Cortex logs, queue database rows, and worker health without modifying production data. Produce a concrete root-cause hypothesis tied to evidence.

## Success Criteria
- Remote process and worker status are checked.
- Recent logs are inspected with timestamps, distinguishing stale errors from current failures.
- Queue database state is inspected for active sessions, pending inbox/outbox, saga rows, session states, and retry/dead rows.
- The failing or waiting state is identified precisely enough to guide a code fix.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
