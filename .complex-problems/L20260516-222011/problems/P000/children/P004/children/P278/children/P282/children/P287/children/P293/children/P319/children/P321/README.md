# Rename stale attach publish helper

## Problem

`SessionRepository._publish_attach_request_after_transaction(...)` no longer publishes an external effect. It records an attach transition and durable outbox effect, then returns outbox-pending metadata. The stale name can mislead future changes back toward repository-owned delivery.

## Success Criteria

- Rename `_publish_attach_request_after_transaction` to a term that reflects durable attach transition/outbox recording.
- Update all call sites and tests/source guards if needed.
- Confirm no production method name still suggests repository-owned attach publish.
- Run focused attach/boundary tests or source guards sufficient for the rename.
