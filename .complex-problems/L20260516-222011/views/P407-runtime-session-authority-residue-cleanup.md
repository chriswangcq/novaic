# P407: Runtime session authority residue cleanup

Status: done
Parent: P403
Root: P000
Source Ticket: T395 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P407
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P407/README.md
Ticket(s): T396

## Problem
Runtime session-authority files (`session_repo`, `session_fsm`, `session_outbox`, `session_recovery`, `session_ledger`, `session_observed_events`, `queue_audit`) contain active/finalize/restart/archive generation-related hits. They must be classified or patched so live session mutation never accepts missing/stale/implicit generation.

## Success Criteria
- Inspect all session-authority runtime hits from the P402 guard outputs.
- Patch any live missing/stale/implicit generation compatibility residue.
- Classify safe validators, audit readers, and explicit projections with file evidence.
- Add focused tests for changed live session authority paths.
- Rerun session-authority runtime guards and focused tests.

## Subproblems
- none

## Results
- R390

## Latest Check
C416

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P407/README.md
- Ticket T396: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P407/tickets/T396.md
- Result R390: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P407/results/R390.md
- Check C416: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P407/checks/C416.md

## Follow-ups
- none
