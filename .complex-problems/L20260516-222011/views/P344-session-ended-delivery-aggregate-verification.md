# P344: Session-ended delivery aggregate verification

Status: done
Parent: P336
Root: P000
Source Ticket: T327 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P344
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P344/README.md
Ticket(s): T335

## Problem
After the implementation children land, verify the entire session-ended delivery boundary as an integrated contract rather than isolated snippets. The check should catch "new logic exists but old path is still active" failures.

## Success Criteria
- Run focused session-ended/finalize tests across saga payload builder, handler/client, route schema, repository finalize, and legacy compat guards.
- Exercise at least one valid session-ended delivery path end to end through handler/client/repository fakes or existing route tests.
- Run source guards for forbidden generation fallback expressions in the P336 delivery boundary.
- Record residual risks and explicitly map any remaining upstream defaulting to P337/P339 rather than calling P336 done.

## Subproblems
- none

## Results
- R329

## Latest Check
C350

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P344/README.md
- Ticket T335: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P344/tickets/T335.md
- Result R329: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P344/results/R329.md
- Check C350: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P344/checks/C350.md

## Follow-ups
- none
