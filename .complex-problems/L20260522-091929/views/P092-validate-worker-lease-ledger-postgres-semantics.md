# P092: Validate Worker Lease Ledger Postgres Semantics

Status: done
Parent: P081
Root: P000
Source Ticket: T084 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P092
Body: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P092/README.md
Ticket(s): T087

## Problem
Worker lease event/state/outbox writes are routed through the generic FSM store, but P081 still needs explicit evidence that lease generation, unique state semantics, JSON/timestamp values, and recovery visibility remain correct under the Postgres backend. This belongs under T084 because saga claim/recovery correctness depends on worker lease ownership state.

## Success Criteria
- Worker lease state upserts preserve generation and unique lease identity semantics under Postgres-compatible store behavior.
- Lease event and outbox writes bind JSON values in a Postgres-compatible form while keeping sqlite behavior intact.
- Lease recovery queries can rely on native timestamptz values produced by the ledger/state path.
- Existing worker lease ledger tests remain green.
- Focused tests or a targeted audit report cover Postgres fake-store behavior for state writes, event writes, outbox writes, and duplicate/idempotent event handling.

## Subproblems
- none

## Results
- R083

## Latest Check
C088

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P092/README.md
- Ticket T087: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P092/tickets/T087.md
- Result R083: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P092/results/R083.md
- Check C088: problems/P000/children/P024/children/P028/children/P074/children/P081/children/P092/checks/C088.md

## Follow-ups
- none
