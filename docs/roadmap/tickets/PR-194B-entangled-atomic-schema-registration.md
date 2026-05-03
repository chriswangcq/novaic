# PR-194B — Entangled Atomic Schema Registration and Safe Broadcast

Status: `[implemented]`

## Current-State Analysis

`/v1/schema/register` currently registers each entity independently. A batch can
partially succeed, return `errors`, and still broadcast a partial schema.

## Small Tickets

- [x] Parse the full schema batch before mutating registry/database state.
- [x] Validate the full batch.
- [x] Apply schema DDL as one registration batch.
- [x] Mutate the in-memory registry only after DDL success.
- [x] Broadcast schema only after full success.
- [x] Return non-2xx on validation or migration failure.
- [x] Add regression tests for no partial registry mutation and no broadcast on
      invalid batch.

## Validation

- Entangled schema registration tests.
- Existing Entangled sync/notifier tests: 61 passed.
