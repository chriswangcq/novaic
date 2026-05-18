# P409: Task contracts and handler residue cleanup

Status: done
Parent: P403
Root: P000
Source Ticket: T395 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/README.md
Ticket(s): T398

## Problem
Task/saga contracts and handlers (`react_think`, `react_actions`, `wake_finalize`, `subagent_wake`, `session_handlers`, `cortex_handlers`, `cortex_bridge`) contain round, stack-depth, session-generation, and archive/finalize hits. They must be classified or patched so task-level defaults cannot weaken live session generation boundaries.

## Success Criteria
- Inspect all task contract, saga, handler, and Cortex bridge hits from P402.
- Patch dangerous session-generation defaults or stale archive/finalize behavior.
- Classify round/stack-depth/tool-retry counters as safe only with file evidence.
- Add focused tests for any patched task contract or handler boundary.
- Rerun task/handler guard searches and focused tests.

## Subproblems
- P412: React contract residue classification
- P413: Finalize saga and session handler residue classification
- P414: Cortex handler and bridge residue classification
- P415: Task contract and handler final verification

## Results
- R396

## Latest Check
C422

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/README.md
- Ticket T398: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/tickets/T398.md
- Result R396: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/results/R396.md
- Check C422: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/checks/C422.md

## Follow-ups
- none
