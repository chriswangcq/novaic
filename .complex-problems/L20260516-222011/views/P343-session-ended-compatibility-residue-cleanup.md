# P343: Session-ended compatibility residue cleanup

Status: done
Parent: P336
Root: P000
Source Ticket: T327 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/README.md
Ticket(s): T331

## Problem
Legacy compatibility tests or code paths may still allow finalize/session-ended generation to be missing or zero. Those residues should be removed rather than supported because stale finalize must fail closed.

## Success Criteria
- Search finalize/session-ended delivery code and tests for `session_generation or 0`, `generation=0`, `Missing generation compatibility`, and equivalent fallback patterns.
- Remove or rewrite stale compatibility tests that bless zero generation.
- Keep any broader react-think/react-actions contract cleanup explicitly delegated to P337/P339 if outside the delivery boundary.
- Record a source-guard command that can be reused in the parent check.

## Subproblems
- P345: Direct session-ended delivery residue guard
- P346: Session-ended delivery tests compatibility cleanup
- P347: Upstream react generation default classification

## Results
- R328

## Latest Check
C349

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/README.md
- Ticket T331: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/tickets/T331.md
- Result R328: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/results/R328.md
- Check C349: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/checks/C349.md

## Follow-ups
- none
