# Problem: Session outbox side-effect ownership audit

## Problem

Audit whether wake saga creation, attach-input publishing, recovery archive publishing, and observed wake-created updates are owned by durable outbox rows and idempotent handlers rather than direct ad hoc side effects.

## Success Criteria

- Map session outbox effect types and handlers with file references.
- Identify whether any session side effect bypasses durable outbox ownership.
- Classify remaining direct calls as safe implementation details, risky, or removable.
