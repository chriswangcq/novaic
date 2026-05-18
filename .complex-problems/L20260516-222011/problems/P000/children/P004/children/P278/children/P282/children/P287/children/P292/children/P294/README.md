# Problem: Session dispatch transaction flow audit

## Problem

Audit `SessionRepository.dispatch()` from input append through FSM decision, state transition, outbox effect creation, and return values.

## Success Criteria

- Map dispatch branches and transaction boundaries with file references.
- Identify whether start/attach/buffer paths all use explicit FSM and ledger/outbox effects.
- Flag any direct publish or state mutation inside the wrong boundary.
