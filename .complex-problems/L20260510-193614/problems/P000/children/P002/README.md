# Phase 1 Cortex Operational SQLite Store Substrate

## Problem

Cortex needs a durable operational state substrate before active stack/status and transition logs can move off projection files/local NDJSON.

## Success Criteria

- Add a Cortex-owned SQLite store module with explicit path, clock/id boundaries.
- Create tables for scope events, scope projection, active stack projection, and payload manifest.
- Wire the store through registry/startup without using process memory as authority.
- Add tests for schema initialization, event append, projection upsert/read, idempotency, and manifest basics.
