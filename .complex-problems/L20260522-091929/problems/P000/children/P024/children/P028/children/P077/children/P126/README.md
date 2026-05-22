# Run Production Queue Postgres Health API Worker And Outbox Smokes

## Problem

Production Postgres mode must be verified with safe smoke checks after restart. The checks must prove health/readiness, representative Queue APIs, worker startup, and outbox drain behavior without unsafe business side effects.

## Success Criteria

- Health/readiness checks pass in production Postgres mode.
- Safe task API smoke covers publish/claim/complete/fail or an approved production-safe equivalent.
- Safe saga/session/idempotency smoke covers representative lifecycle behavior or documented safe equivalents.
- Worker and outbox process checks show startup and no tracebacks/error loops.
- Post-smoke DB counts and outbox histograms are recorded.
- Smoke artifacts are redacted.
