# Capture Queue SQLite Production Inventory

## Problem Definition

The queue Postgres migration map must start from the actual production `queue.db` rather than assumptions. The current queue database has multiple FSM/state/outbox groups and is actively used by queue service and workers.

## Proposed Solution

Run read-only inventory on `api`:

1. Capture file metadata, open holders, and queue process owners.
2. Capture tables, indexes, triggers, schema SQL, and row counts from `/opt/novaic/data/queue.db`.
3. Map table groups to local source modules using focused `rg` and file reads.
4. Write a durable inventory artifact locally and copy it to the `api` host.
5. Verify queue service health afterward.

## Acceptance Criteria

- Production queue DB metadata and row counts are recorded.
- Schemas/indexes/triggers are captured or noted absent.
- Runtime owners and open file holders are identified.
- Table groups are mapped to source modules.
- Queue health remains good.
- No queue data is mutated.

## Verification Plan

Use `stat`, `lsof`, `ps`, and `sqlite3` read-only queries on `api`; use `rg` locally for code-owner mapping; write the inventory Markdown artifact; verify `/health` for queue service after inspection.

## Risks

- Large schema output can hide important details if not grouped.
- Live DB can change row counts during inspection; counts are a point-in-time snapshot.
- Read-only commands must avoid VACUUM, DELETE, migration, or any recovery endpoint that mutates data.

## Assumptions

- Point-in-time row counts are sufficient for planning.
- Current workspace source is close enough to deployed queue code for ownership mapping.
