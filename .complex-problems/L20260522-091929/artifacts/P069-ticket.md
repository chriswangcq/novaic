# Fix Entangled Postgres Percent Placeholder Escaping Locally

## Problem Definition

`PostgresDatabase._convert_placeholders` prepares SQLite-style SQL for psycopg by converting unquoted `?` placeholders to `%s`, but it currently leaves literal `%` characters untouched. psycopg parses `%` markers before SQL execution, so DDL containing patterns like `LIKE 'blob://%'` fails schema registration.

## Proposed Solution

Update `_convert_placeholders` so every literal `%` character in the input SQL becomes `%%` in the psycopg SQL string, while preserving the current quote-aware conversion of unquoted `?` to `%s`. Add a regression test that verifies literal percent escaping in DDL and confirms `?` placeholders still convert correctly.

## Acceptance Criteria

- Literal `%` characters are escaped as `%%` in converted Postgres SQL.
- Unquoted `?` placeholders still convert to `%s`.
- Question marks inside quoted SQL strings remain literals.
- A regression test covers DDL with `LIKE 'blob://%'`.
- Focused local Entangled tests pass.

## Verification Plan

Run targeted pytest coverage in `Entangled/packages/server-python`, including the Postgres database boundary tests and nearby schema/runtime tests that exercise adapter assumptions.

## Risks

- Escaping `%` must not corrupt the generated `%s` placeholders introduced from `?`.
- A too-broad change could alter SQLite-mode behavior if applied outside the Postgres adapter path.

## Assumptions

- Entangled SQL input to `_convert_placeholders` is SQLite-style SQL, not already psycopg-formatted SQL.
- Literal `%` should be escaped even inside quoted SQL because psycopg scans the query string for placeholder syntax before the SQL engine interprets quotes.
