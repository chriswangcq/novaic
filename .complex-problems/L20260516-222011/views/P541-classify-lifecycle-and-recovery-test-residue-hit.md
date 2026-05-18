# P541: Classify lifecycle and recovery test residue hits

Status: done
Parent: P535
Root: P000
Source Ticket: T535 (split)
Source Check: none
Package: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P541
Body: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P541/README.md
Ticket(s): T536

## Problem
Classify the high-density test residue hits in lifecycle/finalize/recovery oriented tests. This group covers tests whose purpose is to protect wake finalization, recovery, scope archival, active inbox, and session failure behavior.

Initial file group:
- `tests/test_pr254_finalize_ownership.py`
- `tests/test_pr266_session_recovery_boundary.py`
- `tests/test_pr245_suspected_dead_recovery.py`
- `tests/test_pr311_saga_compensation_outbox_cutover.py`
- `tests/test_pr233_active_inbox_dispatch.py`
- `tests/test_pr247_recovery_outbox_cutover.py`
- `tests/test_scope_end_environment_notifications.py`

## Success Criteria
- Hits for this file group are counted and reconciled against P531 test scan lines.
- Each file gets a purpose/category rationale.
- Tests that preserve important regression coverage are distinguished from stale misleading tests.
- Any stale or misleading test residue becomes a follow-up.

## Subproblems
- none

## Results
- R530

## Latest Check
C564

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P541/README.md
- Ticket T536: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P541/tickets/T536.md
- Result R530: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P541/results/R530.md
- Check C564: problems/P000/children/P004/children/P281/children/P512/children/P532/children/P535/children/P541/checks/C564.md

## Follow-ups
- none
