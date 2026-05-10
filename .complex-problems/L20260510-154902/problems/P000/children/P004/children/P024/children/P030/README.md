# Phase 3.2.2: Emit notification attachment events

## Problem

Environment notification hints are currently represented as legacy context rows. The authoritative fact must become `InputNotificationAttached` events with enough data for replay to recreate the hint.

## Success Criteria

- Notification attachment path appends `InputNotificationAttached`.
- Event payload includes notification id, source kind, and target scope id.
- Tests verify event stream content and replayed notification hint.
- Direct legacy context rows for notification hints are not treated as source-of-truth.
