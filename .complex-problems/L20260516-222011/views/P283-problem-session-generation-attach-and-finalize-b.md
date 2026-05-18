# P283: Problem: Session generation attach and finalize boundary audit

Status: done
Parent: P278
Root: P000
Source Ticket: T275 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283
Body: problems/P000/children/P004/children/P278/children/P283/README.md
Ticket(s): T317

## Problem
Audit how session generation is assigned, advanced, checked during attach, and checked during finalize/session end. Verify that stale attach/finalize events cannot mutate or close the wrong wake/session generation.

## Success Criteria
- Map generation creation and advancement paths with file references.
- Verify attach/finalize handlers require expected generation where needed.
- Identify any fallback path that accepts missing or stale generation.

## Subproblems
- P326: Session generation lifecycle and advancement inventory
- P327: Attach expected-generation validation audit
- P328: Finalize and session-ended generation ownership audit
- P329: Missing or stale generation compatibility residue guard audit

## Results
- R446

## Latest Check
C472

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/README.md
- Ticket T317: problems/P000/children/P004/children/P278/children/P283/tickets/T317.md
- Result R446: problems/P000/children/P004/children/P278/children/P283/results/R446.md
- Check C472: problems/P000/children/P004/children/P278/children/P283/checks/C472.md

## Follow-ups
- none
