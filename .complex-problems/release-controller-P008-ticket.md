# Implement release-controller persistent state store

## Problem Definition

The release-controller needs durable state before it can safely orchestrate releases. It must persist branch heads, run records, current and previous release pointers, promotion candidates, and failure details under a configured state directory using atomic writes.

## Proposed Solution

Add `release_controller.state` with a `ReleaseStateStore` that owns the directory structure below the configured state directory:

- `branch-heads.json`
- `runs/<run-id>.json`
- `releases/<namespace>-current.json`
- `releases/<namespace>-previous.json`
- `candidates/<candidate-id>.json`

Use a write-temp-and-rename strategy for JSON writes. Keep the store synchronous and dependency-free so planner/API code can call it directly and unit tests can use temporary directories.

## Acceptance Criteria

- State store initializes required directories.
- Branch heads can be read, written, and survive store reload.
- Release runs can be created, updated, listed, and fetched by id.
- Current and previous namespace pointers update atomically when a release succeeds.
- Candidate pointers are stored separately from deployed namespace pointers.
- Failed run details persist and survive store reload.

## Verification Plan

- Add targeted unit tests using `tmp_path`.
- Test branch head persistence across store instances.
- Test run create/update/fetch/list behavior.
- Test current and previous pointer rollover.
- Test candidate pointer persistence.
- Test failed run persistence.

## Risks

- Partial writes could corrupt release pointers; the implementation must use atomic replacement.
- State shape must remain compatible with later HTTP status output, so JSON should be explicit and readable.

## Assumptions

- Concurrency locking will be tightened in planner/API execution slices; this ticket only provides atomic file updates for each persisted object.
