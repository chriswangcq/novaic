# P000: IM tool schema cutover to shell

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
`agentctl im` shell commands now implement the IM behavior, but the LLM-facing tool schema still exposes direct `im_read`, `im_reply`, `im_send`, `im_history`, `im_search`, and `im_context`. This keeps the old path active and violates the shell-boundary migration plan.

## Success Criteria
- LLM-visible builtin schemas no longer include direct IM tools.
- Shell schema/no-tool guidance tells agents to use `agentctl im ...` for IM operations.
- Turn-finalizer logic treats `shell` calls containing `agentctl im reply` as reply turn-closers.
- Direct IM executors may remain as internal compatibility for this phase, but guard tests must make them not LLM-visible.
- Tests cover schema set, no-tool warning, and shell IM reply finalization.

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
