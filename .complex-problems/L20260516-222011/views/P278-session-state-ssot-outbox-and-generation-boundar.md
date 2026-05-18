# P278: Session state SSOT outbox and generation boundary audit

Status: done
Parent: P004
Root: P000
Source Ticket: T273 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278
Body: problems/P000/children/P004/children/P278/README.md
Ticket(s): T275

## Problem
Audit whether `tq_session_state`, outbox tables, generation checks, and active session cache/view behavior match the intended FSM model.

## Success Criteria
- Map session state and active session repository roles.
- Identify hidden inputs or state mutations outside explicit FSM/outbox boundaries.
- Classify any residual compatibility paths as safe, risky, or removable.

## Subproblems
- P282: Problem: Session schema and state ownership audit
- P283: Problem: Session generation attach and finalize boundary audit
- P284: Problem: Session outbox side-effect ownership audit
- P285: Problem: Session compatibility and legacy residue audit

## Results
- R471

## Latest Check
C500

## Bodies
- Problem: problems/P000/children/P004/children/P278/README.md
- Ticket T275: problems/P000/children/P004/children/P278/tickets/T275.md
- Result R471: problems/P000/children/P004/children/P278/results/R471.md
- Check C500: problems/P000/children/P004/children/P278/checks/C500.md

## Follow-ups
- none
