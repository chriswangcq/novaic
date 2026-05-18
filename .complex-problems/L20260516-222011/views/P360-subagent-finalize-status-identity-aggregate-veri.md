# P360: Subagent finalize status identity aggregate verification

Status: done
Parent: P354
Root: P000
Source Ticket: T341 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P360
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P360/README.md
Ticket(s): T345

## Problem
After payload, handler, and ordering changes land, P354 needs an aggregate check that the terminal subagent status path no longer has stale finalize or compatibility residue.

## Success Criteria
- Run focused tests covering wake_finalize payloads, subagent handlers, task path contracts, finalize ownership, and saga DAG integration.
- Run source guards for `last_scope_id`, generation defaulting, and missing-generation compatibility in the touched runtime files.
- Verify there is no direct Business status mutation path from finalize tasks that bypasses the new identity contract.
- Record residual risks explicitly, especially recovery/compensation paths delegated to P351.

## Subproblems
- none

## Results
- R337

## Latest Check
C358

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P360/README.md
- Ticket T345: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P360/tickets/T345.md
- Result R337: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P360/results/R337.md
- Check C358: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/children/P360/checks/C358.md

## Follow-ups
- none
