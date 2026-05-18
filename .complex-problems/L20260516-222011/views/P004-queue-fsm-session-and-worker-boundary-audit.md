# P004: Queue FSM session and worker boundary audit

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T273

## Problem
Audit and optimize queue service/session runtime boundaries after the FSM migration: session state SSOT, outbox behavior, worker assembly, old imperative dispatch branches, finalize ownership, and generation checks.

## Success Criteria
- Current queue/FSM entry points and worker roles are mapped.
- Residual active direct-path branches or compatibility shims are identified.
- High-confidence residue is removed or tightened behind explicit tests.
- Focused tests cover dispatch/session/finalize behavior impacted by any changes.

## Subproblems
- P277: Queue FSM and worker topology map
- P278: Session state SSOT outbox and generation boundary audit
- P279: Legacy imperative dispatch and compatibility residue cleanup
- P280: Finalize watchdog and recovery ownership audit
- P281: Queue FSM focused verification

## Results
- R547

## Latest Check
C581

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T273: problems/P000/children/P004/tickets/T273.md
- Result R547: problems/P000/children/P004/results/R547.md
- Check C581: problems/P000/children/P004/checks/C581.md

## Follow-ups
- none
