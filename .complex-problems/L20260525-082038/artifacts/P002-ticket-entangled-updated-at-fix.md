# Fix Entangled updated_at duplicate assignment

## Problem Definition

Production chat messages stop before Runtime because subscriber cannot claim pending Environment notifications. Entangled's Postgres update SQL assigns `updated_at` twice when callers explicitly provide `updated_at` for an entity that also has automatic timestamp tracking.

## Proposed Solution

Fix Entangled's SQL entity store so automatic `updated_at` mutation is appended only when the caller did not explicitly include `updated_at`. Apply the rule consistently to single update, upsert conflict update, batch update, update-where, and CAS update. Add Postgres SQL-generation tests for explicit `updated_at` across those paths.

## Acceptance Criteria

- Entangled no longer emits Postgres `UPDATE` or `ON CONFLICT DO UPDATE` statements that assign `updated_at` twice.
- Explicit caller-provided `updated_at` remains preserved.
- Calls without explicit `updated_at` still auto-touch `updated_at`.
- Targeted Entangled tests pass.

## Verification Plan

Run `python3 -m pytest packages/server-python/tests/test_postgres_entity_write_queries.py` from the `Entangled` submodule, then deploy and verify under P003 that subscriber can claim the stuck production notification.

## Risks

- Existing code may rely on automatic timestamp overriding caller timestamps; this ticket intentionally makes explicit input authoritative.
- Fixing SQL generation may unblock older pending notifications that then create a burst of queue/runtime work.

## Assumptions

- Entangled's `auto_timestamps` contract should not produce invalid SQL when callers include a valid `updated_at` field.
