# Validate Queue Migration Timestamp Binding

## Problem

P075 migration tooling copies timestamp columns as source values for Postgres TIMESTAMPTZ binding, but the current fixture tests do not explicitly assert representative timestamp preservation. The original P075 criteria require JSON/time conversion validation, so timestamp handling needs direct coverage.

## Success Criteria

- Migration tests identify representative timestamp columns across task, saga, session, worker lease, outbox, idempotency, and config tables.
- Copy execution tests assert those timestamp values are preserved in target-bound rows.
- If a timestamp normalization helper is needed, it is explicit and covered; otherwise tests document that ISO timestamp strings are deliberately passed through for Postgres binding.
- Existing migration planner/copy/validation/CLI tests still pass.
