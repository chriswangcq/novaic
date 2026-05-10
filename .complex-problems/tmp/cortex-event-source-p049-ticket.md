# Rewrite archive and summary tests to API lifecycle path

## Problem Definition

Archive and summary tests still use the removed runtime `cortex.scope_end(...)` helper. These tests need to keep validating archive/summary semantics while closing scopes through the event-wired API `scope_end` handler.

## Proposed Solution

- Add small local helpers in the affected tests where useful:
  - create a root scope through Workspace/projection setup when the test is specifically about archived filesystem invariants,
  - close a root scope through `scope_end(ScopeEndRequest(...))`.
- Replace all `cortex.scope_end(...)` calls in `tests/test_archive_invariants.py` with API `scope_end`.
- Replace the remaining runtime facade summary test in `tests/test_pr74_scope_summary_contract.py` with an API-based structural close assertion or remove the obsolete runtime-specific naming.
- Keep the assertion that structural close writes an empty summary.

## Acceptance Criteria

- `tests/test_archive_invariants.py` has no `cortex.scope_end(...)` calls.
- `tests/test_pr74_scope_summary_contract.py` has no `cortex.scope_end(...)` calls.
- Focused archive/summary tests pass.

## Verification Plan

- Static scan the two files for `.scope_end(`.
- Run:
  - `pytest tests/test_archive_invariants.py tests/test_pr74_scope_summary_contract.py -q`

## Risks

- API `scope_end` rejects non-empty structural reports, so old tests that passed reports to runtime close must be adjusted to assert empty-summary structural behavior explicitly.

## Assumptions

- Scope creation through Workspace/projection setup remains acceptable in these tests when the lifecycle behavior under test is the event-wired close path.
