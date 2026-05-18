# P336: Session-ended outbox delivery generation contract

Status: done
Parent: P328
Root: P000
Source Ticket: T324 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/README.md
Ticket(s): T327

## Problem
Session-ended/finalize side effects crossing the outbox boundary must carry enough explicit generation identity for downstream workers. Missing generation should fail closed rather than causing downstream handlers to infer from current active state.

## Success Criteria
- Map session-ended/finalize outbox effect builders, payload schemas, and delivery handlers.
- Verify payloads include expected saga/scope/generation and finalize reason where required.
- Ensure missing expected generation or scope is rejected before publish/delivery.
- Add tests proving outbox delivery preserves generation identity and rejects malformed finalize/session-ended effects.
- Remove stale compat behavior that silently fills missing generation from current state.

## Subproblems
- P340: Session-ended delivery chain inventory
- P341: Wake-finalize payload positive generation
- P342: Session-ended handler client route contract
- P343: Session-ended compatibility residue cleanup
- P344: Session-ended delivery aggregate verification

## Results
- R330

## Latest Check
C351

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/README.md
- Ticket T327: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/tickets/T327.md
- Result R330: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/results/R330.md
- Check C351: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/checks/C351.md

## Follow-ups
- none
