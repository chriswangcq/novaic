# Root/wake initialization and notification event cutover completed

## Summary

P024 completed the first live write-path cutover group. Root scope creation, wake creation, wake archive, and input notification attachment now append ContextEvents through the explicit writer boundary, while legacy scope/meta files remain transitional artifacts for later cleanup.

## Done

- P029 / R020:
  - `/v1/scope/create` emits `RootInitialized` for root scopes.
  - `/v1/scope/create` emits `WakeStarted` for wake child scopes.
  - `/v1/scope/end` emits `WakeArchived` before wake archive.
  - Idempotent retries do not duplicate lifecycle events.
- P030 / R021:
  - `/v1/scope/append_input` emits `InputNotificationAttached`.
  - Notification events include notification id, `im_message` source kind, and target scope id.
  - Repeated input append requests do not duplicate events.
- P031 / R022:
  - Audited root/wake/notification boundaries.
  - Confirmed remaining legacy writes are transitional artifacts owned by P028 cleanup or unrelated Phase 3 children.

## Verification

- Focused lifecycle/notification tests:
  - Latest focused P024 audit: `10 passed in 0.31s`
- Full Cortex suite:
  - Latest result: `433 passed in 0.63s`

## Known Gaps

- Context append/batch event cutover remains open in P025.
- Tool step event cutover remains open in P026.
- Skill lifecycle event cutover remains open in P027.
- Legacy source-write cleanup remains open in P028.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_lifecycle.py`
