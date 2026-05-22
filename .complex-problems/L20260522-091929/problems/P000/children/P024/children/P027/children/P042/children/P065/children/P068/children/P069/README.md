# Fix Entangled Postgres Percent Placeholder Escaping Locally

## Problem

The Entangled Postgres adapter currently converts SQLite-style `?` placeholders to psycopg `%s` placeholders but leaves literal `%` characters unchanged. DDL such as `CHECK(locator LIKE 'blob://%')` is therefore interpreted by psycopg as an invalid placeholder marker during schema registration.

This child belongs under P068 because production readiness is blocked until the adapter behavior is fixed and tested locally.

## Success Criteria

- `PostgresDatabase._convert_placeholders` escapes literal `%` as `%%` for psycopg.
- Existing `?` to `%s` conversion outside quoted SQL strings is preserved.
- A regression test covers DDL containing a literal percent pattern such as `LIKE 'blob://%'`.
- Focused Entangled tests for the Postgres database boundary and nearby schema/runtime behavior pass locally.
- The local patch is limited to the adapter behavior and its tests.
