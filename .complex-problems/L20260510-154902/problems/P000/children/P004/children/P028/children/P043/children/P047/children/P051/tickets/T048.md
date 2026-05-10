# Migrate miscellaneous runtime lifecycle tests

## Problem Definition

Remaining miscellaneous tests use the removed runtime `cortex.scope_end(...)` helper for convenience. These tests are not about runtime lifecycle ownership, so they should close scopes through the event-wired API path or a clearly named projection setup.

## Proposed Solution

- Replace runtime `cortex.scope_end(...)` calls in:
  - `tests/test_engine_wiring.py`
  - `tests/test_compaction_meta.py`
- Use `scope_end(ScopeEndRequest(...))` with local test registry/lock setup.
- Keep scope creation as Workspace setup where the test is not about create-event behavior.
- Confirm `tests/test_cortex_chaos.py` no longer has runtime lifecycle helper residue after previous child work.

## Acceptance Criteria

- The three miscellaneous test files have no `.scope_create(` or `.scope_end(` calls.
- Focused miscellaneous tests pass.
- Original assertions about engine config, archive meta, and chaos churn remain meaningful.

## Verification Plan

- Static scan:
  - `rg -n "\\.scope_create\\(|\\.scope_end\\(" tests/test_engine_wiring.py tests/test_compaction_meta.py tests/test_cortex_chaos.py`
- Run focused tests:
  - `pytest tests/test_engine_wiring.py tests/test_compaction_meta.py tests/test_cortex_chaos.py -q`

## Risks

- API `scope_end` rejects non-empty reports, so runtime-helper report strings must be dropped rather than reintroduced through a compatibility shim.

## Assumptions

- These tests do not require testing root creation events; Workspace setup is sufficient for their non-lifecycle focus.
