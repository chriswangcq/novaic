# Problem: Session repository transaction and effect orchestration inventory

## Problem

Inspect `SessionRepository` write paths to understand transaction grouping, FSM decision usage, outbox creation, input consumption, and any publish-after-transaction behavior.

## Success Criteria

- Map dispatch/finalize/restart/rebuild write flows with file references.
- Identify which writes happen inside global DB transactions and which publishes happen after transaction.
- Flag any hidden or duplicated state mutation path.
