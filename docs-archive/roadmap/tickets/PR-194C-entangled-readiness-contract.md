# PR-194C — Entangled Readiness Contract

Status: `[implemented]`

## Current-State Analysis

`/v1/health` reports process liveness and current entity count. It does not
separate "process is alive" from "required schema is ready".

## Small Tickets

- [x] Preserve `/v1/health` as liveness.
- [x] Add `/v1/ready` for schema readiness.
- [x] Support optional required entity checks.
- [x] Return non-2xx when required schema is missing.
- [x] Add tests for empty schema, non-empty schema, and required entity checks.

## Validation

- Entangled health/readiness tests: covered by the 61-test Entangled suite.
