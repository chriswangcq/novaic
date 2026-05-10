# Phase 3.2: Cut root/wake initialization and notifications to events

## Problem

Root and wake initialization plus attached input notifications must append ContextEvents as authoritative facts. Legacy scope files may still be emitted only as projection/debug artifacts during the transition.

## Success Criteria

- Root/wake creation appends `RootInitialized` and `WakeStarted` events.
- Input notification attachment appends `InputNotificationAttached` events.
- Event payloads contain enough explicit information to rebuild notification hints and active wake stack.
- Tests verify event stream contents for these paths.
