# P353: Cortex scope_end identity contract

Status: done
Parent: P350
Root: P000
Source Ticket: T339 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P353
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P353/README.md
Ticket(s): T340

## Problem
`task_queue/handlers/cortex_handlers.py::handle_cortex_scope_end` archives Cortex scope state, acknowledges input notifications, removes bridges, and marks participants completed. Determine whether this mutation is structurally safe because it is keyed only by immutable scope identity/path, or add explicit expected wake/session identity checks before mutation.

This child belongs under P350 because Cortex `scope_end` is the main finalize mutation path that can archive or acknowledge state from a stale finalize task.

## Success Criteria
- Inspect `handle_cortex_scope_end`, CortexBridge calls, and the payload built by `wake_finalize` for `cortex.scope_end`.
- Either implement missing identity validation for scope/generation or document with code-backed evidence why the existing immutable scope path makes stale active-session mutation impossible.
- Add tests for missing/stale identity if validation is required.
- No missing identity payload is silently treated as valid when the mutation depends on that identity.

## Subproblems
- none

## Results
- R333

## Latest Check
C354

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P353/README.md
- Ticket T340: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P353/tickets/T340.md
- Result R333: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P353/results/R333.md
- Check C354: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P353/checks/C354.md

## Follow-ups
- none
