# Map Core SQLite Migrations and Close Remaining Residue

## Problem Definition

After Postgres provisioning, SQLite residue cleanup, and LLM Factory cutover, the remaining SQLite files include higher-risk state owners and projections: `queue.db`, `entangled.db`, `gateway.db`, `cortex/operational.sqlite3`, plus the live-empty `device.db` auxiliary path. These cannot be safely migrated by table copy alone because they encode queue FSM/outbox/lease semantics, Entangled entity sync behavior, auth state, and Cortex projection/cache behavior.

## Proposed Solution

Produce and close the remaining migration/residue work as separate checkable tracks:

1. Map `queue.db` semantics to Postgres transactions, JSONB, indexes, row locking, and advisory-lock behavior before any cutover.
2. Document Entangled migration requirements, including schema registration, sync versions, entity JSON representation, and WebSocket/sync impact.
3. Classify Gateway and Cortex stores as migrate/defer/projection and define the eventual Postgres boundary.
4. Resolve or schedule the `device.db` live-empty residue by either proving safe removal after restart or updating Device service code so it stops creating misleading empty tables.
5. Keep owner notes and backup coverage for every SQLite file that remains non-migrated.

## Acceptance Criteria

- Queue migration semantics are mapped before any implementation ticket can cut it over.
- Entangled migration requirements are documented with schema/sync-version risks.
- Gateway and Cortex dispositions are explicit and evidence-backed.
- `device.db` has a concrete closure path rather than remaining unexplained empty state.
- Remaining SQLite state owners are documented as retained/deferred with backup expectations.
- No high-risk SQLite state owner is migrated in this ticket.

## Verification Plan

Inspect code paths and table schemas for queue, entangled, gateway, cortex, and device; write a production migration/residue plan on `api`; update the central SQLite classification note if needed; create follow-up child problems where implementation is too risky for this planning ticket.

## Risks

- Naive queue migration can break idempotency, lease ownership, outbox processing, or recovery behavior.
- Entangled migration can corrupt sync-version semantics or entity schemas if schema registration is not mapped first.
- Removing `device.db` without changing startup code can simply recreate it or break SSH-key endpoints.

## Assumptions

- The immediate safe scope is mapping/planning plus explicit residue closure paths, not cutting over queue or Entangled.
- LLM Factory is already cut over and does not need further work in P004.
