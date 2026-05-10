# Phase 1.1: Define ContextEvent schema and validation

## Problem

Create the deterministic ContextEvent domain model for Cortex. This belongs under Phase 1 because append/read storage cannot be trustworthy until the event envelope, valid event types, canonical semantic body, and validation errors are explicit.

## Success Criteria

- ContextEvent envelope fields are represented in code with explicit schema version, event id, stream id, root scope id, sequence, idempotency key, occurred_at, actor, type, payload, and optional generation/version data if needed.
- Valid event types match the Phase 0 design document closely enough for later write/read cutover.
- Validation rejects malformed event types, non-object payloads, invalid stream/root identity, non-positive sequence, and missing required fields.
- Canonical semantic body comparison is deterministic and excludes generated fields that should not affect idempotency checks.
- Unit tests cover valid event creation, malformed events, canonical body equality, and deterministic serialization.
