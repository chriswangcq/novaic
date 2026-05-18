# Attach Outbox Published Status Failure Ticket

## Problem Definition

`test_outbox_records_start_and_published_attach_effects_after_cutover` expects attach outbox effects to be `published`, but current behavior leaves the attach effect `pending`.

## Proposed Solution

Inspect the test setup, `SessionOutboxDispatcher.drain_pending`, and session repository dispatch behavior to determine whether attach effects should be explicitly drained in the test or auto-published by dispatch.

## Acceptance Criteria

- Root cause is recorded with source/test references.
- Minimal correct code/test update is applied.
- The specific failing test passes.

## Verification Plan

- Run the single failing pytest test.
- Record changed files and command output.

## Risks

- If attach effects should be immediately published, updating the test to accept pending would hide a production bug.

## Assumptions

- Session dispatch writes durable outbox effects; publication may be owned by explicit dispatcher draining rather than repository dispatch itself.
