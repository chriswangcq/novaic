# P012 Success Check

## Summary

P012 is successful. The release-controller now has a branch head poller with injectable head providers, persisted changed-head tracking, unchanged/unmatched skips, poll-triggered planner execution, and tests that avoid network access.

## Evidence

- `BranchPoller` reads heads through an injectable provider.
- `GitBranchHeadProvider` parses `git ls-remote --heads` output through `parse_ls_remote_heads`.
- Changed `main` heads create `TriggerKind.POLL` runs and persist branch heads.
- Unchanged heads skip without creating duplicate runs.
- `release/*` heads create candidate-only poll runs.
- Unmatched branches skip without recording branch heads.
- Preview branch polling was verified directly: `preview/pr-9` planned namespace `preview-pr-9` and persisted the head.
- Poll-triggered `preview/prod` resolution fails through planner safety checks.
- Verification ran and passed: `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`.

## Criteria Map

- Poller can read branch heads through injectable provider: covered by `InMemoryBranchHeadProvider` tests.
- Persist changed branch heads: covered by `test_poll_changed_main_creates_poll_run_and_persists_head` and preview direct check.
- Unchanged heads do not create duplicates: covered by `test_poll_unchanged_head_skips_duplicate_run`.
- Changed `main`, `preview/*`, and `release/*` create planner-backed runs: covered by main test, release test, and preview direct check.
- Poll-triggered runs use `TriggerKind.POLL`: covered by main and release tests.
- Poll-triggered execution cannot target prod: covered by `test_poll_trigger_cannot_resolve_prod`.
- Provider parsing without network: covered by `test_parse_ls_remote_heads`.

## Execution Map

- Added poller and provider code.
- Added shared executor and refactored HTTP API to use it.
- Added six poller tests.
- Ran all release-controller tests.

## Stress Test

- The prod-resolution test uses `preview/prod` with a permissive namespace template, proving the planner guard still blocks branch-driven prod even through the poller.
- The unchanged-head test proves the poller does not create duplicate runs for already-observed commits.

## Residual Risk

- There is still no long-running scheduler loop. That is acceptable for this core slice because deployment integration can call `poll_once()` from a timer without changing release semantics.

## Result IDs

- R007
