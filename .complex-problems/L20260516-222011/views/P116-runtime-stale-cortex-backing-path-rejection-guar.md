# P116: Runtime Stale Cortex Backing Path Rejection Guard

Status: done
Parent: P114
Root: P000
Source Ticket: T108 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P116
Body: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P116/README.md
Ticket(s): T110

## Problem
Runtime shell command handling must reject or block direct use of copied `novaic-cortex-sandbox-*` backing paths so old tool output cannot be pasted into later shell turns and silently break.

## Success Criteria
- Locate the runtime shell command guard that detects stale Cortex backing paths.
- Verify the guard catches `/tmp/novaic-cortex-sandbox-*` or equivalent ephemeral backing paths.
- Run focused tests for stale-path rejection.
- Fix any missing guard coverage without adding compatibility fallback behavior.

## Subproblems
- none

## Results
- R105

## Latest Check
C119

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P116/README.md
- Ticket T110: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P116/tickets/T110.md
- Result R105: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P116/results/R105.md
- Check C119: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P116/checks/C119.md

## Follow-ups
- none
