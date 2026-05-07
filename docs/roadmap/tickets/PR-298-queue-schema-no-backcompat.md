# PR-298 — Queue Schema No-Backcompat Cutover

Status: Closed

## Goal

Collapse the queue schema migration ladder into a current-schema-only contract:
fresh databases are initialized, current-version databases are verified, and old
schema versions fail fast.

## Scope

- Remove old `from_version < ...` migration branches from `schema.py`.
- Fail clearly for old schema versions instead of mutating historical data.
- Replace old migration tests with fresh-schema/current-version guards.
- Remove obsolete migration expectations for retired tables/effect rewrites.

## Dependencies

- PR-296 deployment migration plan.

## Risks

- Existing old local databases must be reset or migrated out of band before this
  code boots. This is intentional under the user's no-backcompat requirement.

## Acceptance Criteria

- `init_schema()` no longer rewrites old wake outbox rows or drops old tables as
  an upgrade path.
- Old schema versions raise an explicit error.
- Fresh schema tests cover the absence of retired tables and current version.

## Verification

- Schema/unit tests.
- Full runtime suite.
- Grep for old migration idempotency keys and retired migration branches.

## Closure Notes

- Collapsed `init_schema()` to a current-schema-only contract: fresh DBs are
  initialized, current DBs are idempotently checked, and old/missing-version
  existing DBs raise `RuntimeError`.
- Removed the old `run_migration()` ladder and old wake outbox rewrite logic.
- Replaced old migration tests with fail-fast/fresh-schema guards.
- Updated deployment migration docs to record the no-backcompat rollback
  boundary.
- Verified by targeted schema tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 364 passed.
