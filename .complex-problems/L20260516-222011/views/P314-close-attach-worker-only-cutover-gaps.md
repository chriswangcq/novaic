# P314: Close attach worker-only cutover gaps

Status: done
Parent: P312
Root: P000
Source Ticket: none (none)
Source Check: C311
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/README.md
Ticket(s): T302

## Problem
The attach worker-only cutover is partially implemented but not verified. Dispatch still crashes on a stale `task_id` log assumption, the wrapper boundary test still guards an older source shape, and focused compile/test verification must be rerun with correct paths. Close only these concrete gaps without expanding scope.

## Success Criteria
- Active attach dispatch no longer references `task_id` and returns a stable worker-only result with `delivery=outbox_pending` and `outbox_id`.
- Session outbox dispatcher no longer exposes or uses a repository-owned `publish_attach_input_effect` wrapper.
- Boundary/source tests assert the current generic outbox wrapper shape rather than stale single-effect assumptions.
- Correct focused py_compile and pytest commands pass from the `novaic-agent-runtime` working directory.
- No new eager attach publish path is introduced.

## Subproblems
- P315: Remove stale attach task_id assumption
- P316: Update session outbox boundary source guards
- P317: Verify attach worker-only cutover after patches

## Results
- R298

## Latest Check
C315

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/README.md
- Ticket T302: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/tickets/T302.md
- Result R298: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/results/R298.md
- Check C315: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/checks/C315.md

## Follow-ups
- none
