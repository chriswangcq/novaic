# Cut root/wake initialization and notification attachment to events

## Problem Definition

Root/wake initialization and input notification attachment must become ContextEvent writes. This ticket covers the first live write-path cutover and must avoid leaving a hidden legacy source-of-truth path for these facts.

## Proposed Solution

- Locate the exact root/wake initialization paths and notification append paths.
- Wire `ContextEventWriter` at those boundaries with explicit request identity and injected store dependencies.
- Append `RootInitialized`, `WakeStarted`, `WakeArchived`, and `InputNotificationAttached` where applicable.
- Ensure duplicate/retry behavior uses stable idempotency keys.
- Add tests that assert event log rows are written.
- Keep legacy files only as transitional projection/debug artifacts until P028 cleans them.

## Acceptance Criteria

- Root/wake initialization emits the correct events.
- Notification attachment emits `InputNotificationAttached`.
- Event stream content is tested.
- No endpoint silently bypasses event append for these facts.
- Existing Cortex tests remain green.

## Verification Plan

- Add focused tests for the changed initialization/notification paths.
- Run relevant context/API tests.
- Run full `novaic-cortex` suite.
- Static scan changed paths for `ContextEventWriter` usage and old direct-only behavior.

## Risks

- Root/wake initialization is spread across workspace, runtime, and API/service callers; if this is larger than expected, split into smaller child tickets before editing deeply.

## Assumptions

- Old data migration is not required; user approved deleting old data and full cutover.
