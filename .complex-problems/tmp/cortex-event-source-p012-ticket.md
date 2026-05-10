# Implement ContextEvent store read side

## Problem Definition

The ContextEvent schema exists, but there is no store component that owns the event-log path and can read/replay persisted JSONL rows into validated `ContextEvent` objects.

## Proposed Solution

- Add `novaic-cortex/novaic_cortex/context_event_store.py`.
- Define `ContextEventStore` with a `Workspace` dependency and a deterministic `event_log_path(root_scope_path)` helper.
- Implement `read_events(root_scope_path)`:
  - missing event log returns `[]`;
  - empty/blank lines are ignored;
  - each JSONL row is parsed as JSON object;
  - each row is validated through `ContextEvent.from_dict`;
  - rows are returned in file order as `ContextEvent` objects.
- Define a clear `ContextEventStoreError` for store-level parse/read failures while preserving schema errors where useful.
- Add tests for path construction, empty read, valid ordered read, malformed JSON, non-object JSON, and invalid envelope.

## Acceptance Criteria

- Store read module exists and depends only on Workspace IO plus ContextEvent validation.
- Missing logs are safe empty streams.
- Corrupt persisted rows are loud failures, not silently skipped.
- Focused read tests pass.

## Verification Plan

- Run focused read tests.
- Run existing event model tests.
- Review static search to ensure the store read side does not write files or generate ids/time.

## Risks

- Store-level errors could hide schema error details; preserve enough context in messages.
- Path shape must remain obviously projection-independent and root-stream-owned.

## Assumptions

- Root scope path is a logical Cortex path such as `/ro/active/<root>`.
- Append behavior is implemented in P013.
