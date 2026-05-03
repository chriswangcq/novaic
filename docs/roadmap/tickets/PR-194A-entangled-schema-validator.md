# PR-194A — Entangled Schema Validator and SQL Identifier Guard

Status: `[implemented]`

## Current-State Analysis

Entangled currently accepts schema specs, converts them to `SqlEntityDef`, and
immediately mutates store/schema state. Invalid SQL identifiers can reach DDL,
as shown by the previous `agent-activity-records.order` failure.

## Small Tickets

- [x] Add an Entangled-owned schema validator.
- [x] Reject invalid SQL table/column identifiers and SQLite reserved keywords.
- [x] Validate `id_field`, `key_params`, `default_order`, default-not-in filters,
      duplicate fields, duplicate tables, and parent field references where
      Entangled has enough information.
- [x] Add unit tests for accepted existing Business/Device-style shapes and
      rejected bad identifiers.
- [x] Confirm no code path relies on upstream-only validation.

## Validation

- Entangled schema validator/registration tests.
- Existing Entangled unit tests: 61 passed.
