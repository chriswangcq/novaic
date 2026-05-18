# Attach session outbox delivery audit

## Problem

Audit `SessionOutboxDispatcher` attach delivery to verify it requires `expected_session_generation`, preserves it into downstream task/runtime payload, and fails closed on missing generation.

## Success Criteria

- Map attach outbox payload parsing and task/runtime payload creation with file references.
- Verify missing `expected_session_generation` is rejected before delivery.
- Verify delivered payload contains both expected scope and expected generation.
- Identify tests/guards for session outbox attach payload shape.
