# Implement release-controller branch head polling

## Problem Definition

The release-controller core currently supports manual API triggers but does not yet poll branch heads. It needs a deterministic polling component that detects changed branch heads, persists observed heads, skips unchanged commits, and reuses the existing planner/runner path for eligible branch releases.

## Proposed Solution

Add `release_controller.poller` with:

- a `GitBranchHeadProvider` protocol and subprocess implementation for `git ls-remote --heads`
- an in-memory provider suitable for unit tests
- a `BranchPoller` that matches concrete branch names against configured branch rules
- changed-head detection against `ReleaseStateStore.read_branch_heads()`
- dry-run/execution support through `ReleasePlanner` and `CommandRunner`
- explicit skipped records for unmatched or unchanged branches where useful for observability

Keep the poller synchronous and single-iteration testable. A later deployment slice can decide whether to run it as a background loop or external scheduled call.

## Acceptance Criteria

- Poller can read branch heads through an injectable provider.
- Poller persists changed branch heads.
- Unchanged branch heads do not create duplicate runs.
- Changed `main`, `preview/*`, and `release/*` heads create planner-backed runs.
- Poll-triggered runs use `TriggerKind.POLL`.
- Poll-triggered execution cannot target prod.
- Tests cover changed, unchanged, release candidate, unmatched branch, and provider input behavior without network access.

## Verification Plan

- Add unit tests with an in-memory branch head provider.
- Run all release-controller tests.
- Run a direct import check for `BranchPoller`.

## Risks

- Poller must not reimplement branch safety rules; it should call `ReleasePlanner`.
- Git provider parsing must handle normal `git ls-remote --heads` output without carrying network behavior into tests.

## Assumptions

- Background scheduling is not required in this ticket; one poll iteration is enough for service/API integration.
