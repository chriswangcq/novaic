# Queue DSN Repair Check

## Summary

`P119` is not successful yet. `R109` satisfies the DSN repair and Postgres container criteria, but Queue Service still does not start and `/health` plus `/ready` do not pass.

## Blocking Gaps

- Acceptance criterion "Queue Service starts with Postgres backend using the DSN file" is not met because the process exits during fresh Postgres schema initialization.
- Acceptance criterion "`/health` passes" is not met because the service never binds the staging loopback port.
- Acceptance criterion "`/ready` passes" is not met for the same reason.
- The remaining blocking gap is a code defect in `init_postgres_schema`: the expected missing `config` table probe on a fresh database leaves the Postgres transaction aborted because the exception path does not roll back before the DDL loop.

## Result IDs

- `R109`
