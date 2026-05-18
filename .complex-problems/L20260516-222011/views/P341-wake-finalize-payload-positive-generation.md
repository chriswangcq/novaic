# P341: Wake-finalize payload positive generation

Status: done
Parent: P336
Root: P000
Source Ticket: T327 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P341
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P341/README.md
Ticket(s): T329

## Problem
`wake_finalize` payload construction must not silently convert missing `session_generation` to `0`. A missing or non-positive generation should become an explicit validation failure before a `session.ended` effect is published.

## Success Criteria
- Remove `session_generation or 0` fallback from `task_queue/sagas/wake_finalize.py`.
- Ensure `_build_session_ended_payload(...)` requires positive generation and preserves scope/finalize reason/remaining stack.
- Add tests for valid positive generation and missing/zero generation rejection.
- Run focused tests and source guards proving the wake-finalize payload builder no longer emits zero-generation session-ended payloads.

## Subproblems
- none

## Results
- R323

## Latest Check
C344

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P341/README.md
- Ticket T329: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P341/tickets/T329.md
- Result R323: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P341/results/R323.md
- Check C344: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P341/checks/C344.md

## Follow-ups
- none
