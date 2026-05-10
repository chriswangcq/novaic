# Delete Workspace Resolve Active Scope Path

## Problem Definition

`Workspace.resolve_active_scope_path(...)` remains as lower-level file-walk stack code after all live API authority was cut to SQLite active-stack projection. Static search shows no production caller outside its own definition, but tests and docs still reference the old name. The user prefers physical deletion over compatibility residue.

## Proposed Solution

- Audit all `resolve_active_scope_path` references.
- Delete `Workspace.resolve_active_scope_path(...)` from `novaic-cortex/novaic_cortex/workspace.py` if no production caller remains.
- Update tests that monkeypatch the old method to rely on static guards / projection assertions instead.
- Leave historical docs untouched unless they are active architecture docs that would mislead current implementation; record doc residue separately if broad docs cleanup is too large for this follow-up.
- Run static search, targeted tests, full Cortex tests, and `py_compile`.

## Acceptance Criteria

- `workspace.py` no longer defines `resolve_active_scope_path(...)`.
- No production code references `resolve_active_scope_path`.
- Runtime tests no longer monkeypatch `resolve_active_scope_path` as if it were a live dependency.
- Static search identifies only historical docs or no matches; any active current docs are updated or listed as follow-up residue.
- Targeted tests, full Cortex suite, and `py_compile` pass.

## Verification Plan

- `rg -n "resolve_active_scope_path" novaic-cortex/novaic_cortex novaic-cortex/tests -S`
- Targeted active-stack/routing tests.
- Full Cortex test suite.
- `python3 -m py_compile $(find novaic-cortex/novaic_cortex -name '*.py' | sort)`

## Risks

- Some old tests may have been asserting absence of usage by monkeypatching the old method; deleting it requires replacing those checks with stronger static guards.
- Historical docs contain old architecture descriptions; cleaning every historical mention may be larger than this code follow-up.

## Assumptions

- No compatibility path should keep the old helper alive.
- Live API routing and stack authority are already covered by SQLite projection tests and guards.
