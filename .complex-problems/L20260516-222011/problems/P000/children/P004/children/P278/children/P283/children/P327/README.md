# Attach expected-generation validation audit

## Problem

Audit attach delivery end to end: dispatch decision, session outbox payload, outbox worker delivery, and saga/task handler validation. Verify stale attach input cannot be delivered to or mutate a newer session generation.

## Success Criteria

- Map attach request creation and payload fields, including expected generation, with file references.
- Verify outbox worker and downstream handler preserve and enforce expected generation.
- Identify whether missing-generation or stale-generation attach payloads are rejected, ignored, or accepted.
- Add or identify tests proving stale attach does not publish/mutate the wrong wake.
