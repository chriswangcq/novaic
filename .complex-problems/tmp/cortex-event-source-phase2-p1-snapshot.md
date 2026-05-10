# Phase 2.1: Projection snapshot and message events

## Problem

Implement the pure projection snapshot skeleton and replay of non-scope message events. This belongs under Phase 2 because every later fold/tool behavior needs a deterministic projection output shape and applied sequence.

## Success Criteria

- A pure projector module accepts ordered `ContextEvent` objects and returns a snapshot with `root_scope_id`, `applied_seq`, `messages`, `stack`, and metadata.
- Projector handles `RootInitialized`, `WakeStarted`, `WakeArchived`, `SystemPromptAdded`, `ContextMessageAppended`, and `InputNotificationAttached`.
- Notification projection renders a hint from `notification_id` and `source_kind` without fetching message bodies.
- Tests cover empty events, simple system/context messages, notification hints, applied sequence, and wake archive stack behavior.
