# Problem: Unify dispatch start-wake transition construction

## Problem

`SessionRepository.dispatch()` has two active implementations for building and recording start-wake durable outbox transitions: ordinary no-active start inside the initial transaction and recovery start after the initial transaction. Both are currently durable, but duplicated construction risks future drift.

## Success Criteria

- Extract or otherwise unify the shared start-wake transition construction/recording logic so ordinary start and recovery start cannot diverge silently.
- Preserve durable outbox authority and required outbox checks.
- Preserve input consumption and recovery archive behavior.
- Add or update focused tests/guards that would fail if duplicate active start-wake construction returns.
