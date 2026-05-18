# P132: Cross-layer context projection regression suite

Status: done
Parent: P003
Root: P000
Source Ticket: T121 (split)
Source Check: none
Package: problems/P000/children/P003/children/P132
Body: problems/P000/children/P003/children/P132/README.md
Ticket(s): T254

## Problem
Projection correctness crosses Cortex and agent-runtime. Separate local tests can pass while the integrated flow still leaks or drops media. A final cross-layer regression suite is needed after child fixes to prove the whole contract holds.

## Success Criteria
- The focused Cortex projection tests pass.
- The focused agent-runtime context tests pass.
- At least one integrated or near-integrated test covers shell screenshot manifest output followed by display/current media projection and later historical replay.
- The final check explicitly verifies no raw base64 appears in text history for display/tool results.
- Residual risks are documented with concrete evidence pointers, not broad confidence claims.

## Subproblems
- P259: Cortex projection regression coverage
- P260: Agent-runtime current versus historical media regression coverage
- P261: Near-integrated screenshot manifest to display replay regression
- P262: Final cross-layer projection marker scan

## Results
- R270

## Latest Check
C285

## Bodies
- Problem: problems/P000/children/P003/children/P132/README.md
- Ticket T254: problems/P000/children/P003/children/P132/tickets/T254.md
- Result R270: problems/P000/children/P003/children/P132/results/R270.md
- Check C285: problems/P000/children/P003/children/P132/checks/C285.md

## Follow-ups
- none
