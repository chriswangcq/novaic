# Record Queue Postgres Post-Smoke Counts

## Problem

After API smokes run, Queue Postgres table counts and target public info must be recorded so P109/P106 have durable evidence of what changed. This child belongs under T106 because count/reporting evidence is separate from endpoint success.

## Success Criteria

- Post-smoke counts are recorded for Queue migration tables.
- Target public info is recorded with DSNs/secrets redacted.
- Counts are tied to the smoke run artifact or command evidence.
- Any count query failure is recorded with enough detail to diagnose without exposing secrets.
