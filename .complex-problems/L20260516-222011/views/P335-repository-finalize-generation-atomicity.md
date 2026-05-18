# P335: Repository finalize generation atomicity

Status: done
Parent: P328
Root: P000
Source Ticket: T324 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P335
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P335/README.md
Ticket(s): T326

## Problem
Repository methods that clear active state, record session ended/finalize events, or restart pending input must verify the current active session generation inside the same mutation boundary. Otherwise stale saga completion can clear or restart a newer wake.

## Success Criteria
- Map repository methods that mutate active session state during finalize/session-ended/restart/rebuild.
- Verify or implement generation/scope checks inside the same transaction as active clearing or pending restart projection.
- Remove unsafe implicit active-generation lookup or generation fallback behavior for finalize mutations.
- Add tests proving stale finalize/session-ended repository calls do not clear newer active sessions.
- Add tests proving valid finalize still clears/archives the intended active generation.

## Subproblems
- none

## Results
- R321

## Latest Check
C342

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P335/README.md
- Ticket T326: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P335/tickets/T326.md
- Result R321: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P335/results/R321.md
- Check C342: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P335/checks/C342.md

## Follow-ups
- none
