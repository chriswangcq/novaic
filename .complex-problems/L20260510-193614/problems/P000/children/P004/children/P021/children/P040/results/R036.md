# Delete Workspace Active Path File-Walk Helper Result

## Summary

Deleted the remaining production `Workspace.resolve_active_scope_path(...)` helper and removed tests' dependency on monkeypatching that helper. Current routing tests now assert the helper is absent and continue to prove route correctness through SQLite active stack projection results. Current architecture docs were updated away from file-walk control-stack wording; remaining text hits are limited to regression assertions and historical dated/roadmap documents.

## Done

- Removed `Workspace.resolve_active_scope_path(...)` from `novaic-cortex/novaic_cortex/workspace.py`.
- Updated `novaic-cortex/tests/test_context_event_api_steps_write.py` so active write routing tests assert the helper is physically absent and verify returned/event scope paths.
- Updated `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py` so reopened-workspace LIFO tests assert the helper is physically absent and verify SQLite projection behavior.
- Updated current docs:
  - `docs/architecture/cortex.md`
  - `docs/cortex/internal-api-schemas.md`
  - `docs/cortex/invariants.md`
  - `docs/cortex/scope-lifecycle.md`
  - `docs/cortex/hardening-checklist.md`
  - `docs/cortex/state-authority-implementation-plan.md`
  - `docs/architecture/agent-loop-control-plane-consistency.md`

## Verification

- Production static audit: `rg -n "resolve_active_scope_path|_collect_active_stack" novaic-cortex/novaic_cortex -S` returned no matches.
- Current-doc static audit: `rg -n "resolve_active_scope_path|_collect_active_stack" docs/architecture/cortex.md docs/cortex/internal-api-schemas.md docs/cortex/invariants.md docs/cortex/hardening-checklist.md docs/cortex/scope-lifecycle.md docs/cortex/state-authority-implementation-plan.md docs/architecture/agent-loop-control-plane-consistency.md -S` returned no matches.
- Test monkeypatch audit: `rg -n "monkeypatch\\.setattr\\([^\\n]*resolve_active_scope_path|fail_resolve_active_scope_path|resolve_active_scope_path" novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_context_event_api_skill_lifecycle.py -S` now only finds `hasattr(..., "resolve_active_scope_path")` absence assertions.
- Targeted tests passed: `42 passed in 0.60s`.
- Full Cortex tests passed: `462 passed in 1.49s`.
- Python compile passed: `python3 -m py_compile $(find novaic-cortex/novaic_cortex -name '*.py' | sort)`.

## Known Gaps

- Historical documents still mention the deleted helper as past-state context:
  - `docs/cortex/architecture-review-2026-04-17.md`
  - `docs/roadmap/tickets/PR-234A-cortex-authoritative-stack-source.md`
  - `docs/roadmap/tickets/PR-43-scope-chain-previous-id.md`
- Those hits are intentionally classified as historical records, not current runtime guidance.

## Artifacts

- Result body: `.complex-problems/tmp/impl-p3e-followup-result.md`
