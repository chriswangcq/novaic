# Ticket: Map Cortex Archive Diagnostics Persistence

## Problem Definition

Before implementing P373, map the exact code path that writes `WakeArchived` and active-stack finalize records so diagnostic metadata can be added in the right location without mixing semantic and diagnostic `remaining_stack` shapes.

## Proposed Solution

Read Cortex API helper functions around `ScopeEndRequest`, `_append_wake_archived_event`, `_semantic_remaining_stack_after_archive`, and `scope_end`, plus focused context event tests.

## Acceptance Criteria

- Source map identifies current event payload shape and persistence helper.
- Source map identifies where diagnostics should be nested or named.
- Source map identifies tests to update/add.

## Verification Plan

- Read-only source inspection.
- Record result with file references and proposed change point.

