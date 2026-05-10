# P005: Phase 4: Prepare/read-path cutover from events

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P005
Body: problems/P000/children/P005/README.md
Ticket(s): T052

## Problem
Cut `prepare_for_llm`, context status, stack reads, and relevant Runtime bridge behavior over to event-source/projection semantics instead of DFS file source semantics.

## Success Criteria
- `prepare_for_llm` uses event replay/projection as the primary path.
- DFS file traversal is removed as source-of-truth or restricted to explicit repair/debug projection checks.
- Runtime prepare flow no longer depends on call-time DFS scan of legacy source files.
- Tests prove prepared messages match event semantics across active wake, closed summaries, nested skills, tools, and notifications.

## Subproblems
- P054: Build event projection read adapter
- P055: Cut prepare_for_llm API to event projection
- P056: Cut status usage and stack reads to event semantics
- P057: Audit DFS read fallback removal

## Results
- R055

## Latest Check
C058

## Bodies
- Problem: problems/P000/children/P005/README.md
- Ticket T052: problems/P000/children/P005/tickets/T052.md
- Result R055: problems/P000/children/P005/results/R055.md
- Check C058: problems/P000/children/P005/checks/C058.md

## Follow-ups
- none
