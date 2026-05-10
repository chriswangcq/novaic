# P000: Cortex LLM DFS context assembly audit

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Audit novaic-cortex LLM context DFS assembly logic and determine whether it correctly assembles open scopes, folded completed scopes, tool projections, summaries, and ordering without hidden stale paths.

## Success Criteria
- Locate the active code path used to assemble LLM context from Cortex workspace state.
- Verify DFS traversal, fold/expand semantics, child summary behavior, and chronological ordering.
- Verify current tests cover the important invariants and run focused tests.
- Identify concrete bugs or residual design risks with file pointers.
- Avoid speculative changes; only recommend or patch if evidence is clear.

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
