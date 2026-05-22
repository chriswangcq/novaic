# Port Saga Lifecycle Mutations And State Locking To Postgres

## Problem

Saga single-row lifecycle operations such as heartbeat, launch, step result append, completion, fail, and cancel rely on transaction boundaries that were sufficient for sqlite but need explicit Postgres saga-state row locking or compare/update semantics. This belongs under T084 because these operations decide and persist saga state after a candidate or direct saga id has been selected.

## Success Criteria

- Postgres `_get_saga_for_update` or equivalent locks the relevant `tq_saga_state` row with `FOR UPDATE` or uses a reviewed compare/update pattern.
- Heartbeat, launch, step result append, completion, fail, and cancel paths read/lock state before lifecycle decisions.
- Postgres JSON fields such as context, step results, and pending steps bind as JSONB-compatible native values where applicable.
- Existing sqlite saga lifecycle tests remain compatible.
- Focused tests cover no-op/loser paths, JSONB binding, and lock SQL shape.
