# P446: Cortex generation and active-state compatibility guard

Status: done
Parent: P420
Root: P000
Source Ticket: T435 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P446
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P446/README.md
Ticket(s): T436

## Problem
Final Cortex verification needs a focused guard for old active-state lookup and missing/stale generation compatibility paths. These paths are dangerous because they can resurrect old session/scope authority semantics.

## Success Criteria
- Save source guard scans for generation, active lookup, stack/scope compatibility, and legacy state words, excluding `.complex-problems`.
- Classify every remaining hit as current explicit contract, test fixture, docs/comment, or unresolved risk.
- Confirm no live Cortex path accepts missing/stale generation where generation is required.
- Confirm no live Cortex path revives old active-state lookup as authoritative state.

## Subproblems
- none

## Results
- R429

## Latest Check
C455

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P446/README.md
- Ticket T436: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P446/tickets/T436.md
- Result R429: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P446/results/R429.md
- Check C455: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P420/children/P446/checks/C455.md

## Follow-ups
- none
