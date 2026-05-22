# Validate Worker Lease Ledger Postgres Semantics

## Problem

Worker lease event/state/outbox writes are routed through the generic FSM store, but P081 still needs explicit evidence that lease generation, unique state semantics, JSON/timestamp values, and recovery visibility remain correct under the Postgres backend. This belongs under T084 because saga claim/recovery correctness depends on worker lease ownership state.

## Success Criteria

- Worker lease state upserts preserve generation and unique lease identity semantics under Postgres-compatible store behavior.
- Lease event and outbox writes bind JSON values in a Postgres-compatible form while keeping sqlite behavior intact.
- Lease recovery queries can rely on native timestamptz values produced by the ledger/state path.
- Existing worker lease ledger tests remain green.
- Focused tests or a targeted audit report cover Postgres fake-store behavior for state writes, event writes, outbox writes, and duplicate/idempotent event handling.
