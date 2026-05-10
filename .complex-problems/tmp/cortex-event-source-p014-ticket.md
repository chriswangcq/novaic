# Implement projection snapshot and message events

## Problem Definition

There is no pure projection module that converts ordered ContextEvents into a snapshot. P014 must create the deterministic projection output shape and replay basic root/wake/message/notification events without Workspace or IM access.

## Proposed Solution

- Add `novaic-cortex/novaic_cortex/context_event_projection.py`.
- Define a projection snapshot dataclass or typed structure with `root_scope_id`, `applied_seq`, `messages`, `stack`, and metadata.
- Implement `project_context_events(events)` for:
  - empty input;
  - `RootInitialized`;
  - `WakeStarted`;
  - `WakeArchived`;
  - `SystemPromptAdded`;
  - `ContextMessageAppended`;
  - `InputNotificationAttached`.
- Render notification hints as system messages using only `notification_id` and `source_kind`.
- Add focused tests for empty projection, simple system/context messages, notification hint, applied sequence, and wake archive stack behavior.

## Acceptance Criteria

- Projection module is pure and takes events as explicit input.
- Output shape includes root id, applied seq, messages, and stack.
- Basic message and notification events replay deterministically.
- Projector does not fetch IM bodies, workspace files, or payload data.
- Focused P014 tests pass.

## Verification Plan

- Run projection tests and event substrate tests.
- Static scan projector module for Workspace/IM/filesystem/legacy DFS source usage.

## Risks

- Snapshot shape can drift from later integration needs; keep it explicit and minimal.
- Notification rendering must not accidentally become an IM read path.

## Assumptions

- Scope fold and tool result behavior will be added in P015/P016.
