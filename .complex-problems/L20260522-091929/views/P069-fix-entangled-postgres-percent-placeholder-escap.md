# P069: Fix Entangled Postgres Percent Placeholder Escaping Locally

Status: done
Parent: P068
Root: P000
Source Ticket: T065 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P069
Body: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P069/README.md
Ticket(s): T066

## Problem
The Entangled Postgres adapter currently converts SQLite-style `?` placeholders to psycopg `%s` placeholders but leaves literal `%` characters unchanged. DDL such as `CHECK(locator LIKE 'blob://%')` is therefore interpreted by psycopg as an invalid placeholder marker during schema registration.

This child belongs under P068 because production readiness is blocked until the adapter behavior is fixed and tested locally.

## Success Criteria
- `PostgresDatabase._convert_placeholders` escapes literal `%` as `%%` for psycopg.
- Existing `?` to `%s` conversion outside quoted SQL strings is preserved.
- A regression test covers DDL containing a literal percent pattern such as `LIKE 'blob://%'`.
- Focused Entangled tests for the Postgres database boundary and nearby schema/runtime behavior pass locally.
- The local patch is limited to the adapter behavior and its tests.

## Subproblems
- none

## Results
- R062

## Latest Check
C064

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P069/README.md
- Ticket T066: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P069/tickets/T066.md
- Result R062: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P069/results/R062.md
- Check C064: problems/P000/children/P024/children/P027/children/P042/children/P065/children/P068/children/P069/checks/C064.md

## Follow-ups
- none
