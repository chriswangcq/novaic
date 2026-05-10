# P000: Cortex state authority audit

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Audit whether the current Cortex service matches the intended shape: Cortex is a state semantics service, while authoritative long-lived state lives in Workspace/LogicalFS-backed files rather than Cortex process memory. Identify what is already true and what remains imperfect, including caches, logs, locks, payloads, context events, scope files, and shell/materialization state.

## Success Criteria
- Map each Cortex state category to its authority: LogicalFS/Workspace, Blob/Object store, process memory cache, external lock, or observability log.
- Confirm whether LLM context state is event-sourced from Workspace/LogicalFS.
- Identify any Cortex process-memory state that could affect correctness after restart.
- Identify any non-LogicalFS persistent state and whether it is authoritative or observational.
- Distinguish real imperfections from acceptable caches/adapters.
- Provide evidence pointers from code and tests.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
