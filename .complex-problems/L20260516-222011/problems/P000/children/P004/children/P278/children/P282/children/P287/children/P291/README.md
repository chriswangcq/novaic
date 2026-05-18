# Problem: Session ledger mutation API inventory

## Problem

Inspect `SessionLedgerRepository` and generic FSM store usage to list all legitimate session event/state/outbox mutation APIs and their explicit dependencies.

## Success Criteria

- List ledger mutation methods and target table/effect categories.
- Verify ID/time inputs are injected at the ledger boundary.
- Identify any ledger method that mixes business decision logic into storage mechanics.
