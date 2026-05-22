# Run Entangled Postgres REST Smoke Suite And Report

## Problem

With the Postgres-mode runtime running, run representative REST smokes and capture a redacted report. This belongs under `P051` because production cutover needs concrete API proof, not only process readiness.

## Success Criteria

- REST smokes cover health/readiness plus representative list/read, singleton upsert/read, stream append/query, update, delete, and CAS or equivalent rowcount-sensitive behavior.
- Schema registration succeeds or existing registered schemas are proven available.
- Smoke output includes endpoint statuses, entity/table names, counts, and mutation cleanup evidence.
- Auth/service-token requirements are satisfied safely or a narrow blocker/follow-up is created.
- Report is written under ledger artifacts and contains no DSNs, service tokens, cookies, or env-file contents.
- Staging process is stopped or confirmed safe to leave only if explicitly intended.
