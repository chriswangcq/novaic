# Verify Phase 1 Operational Store Substrate

## Problem Definition

Phase 1 is only complete if the new operational SQLite substrate is implemented, explicitly wired at the Cortex boundary, and not left as unused or half-integrated code. The phase needs a residue audit before the parent `P002` can be closed.

## Proposed Solution

Run verification and static audits across the Phase 1 changes:

- Run targeted Cortex tests.
- Compile/import relevant modules.
- Search for missing `operational_sqlite_path` wiring, hidden in-memory fallback, and unregistered factory call sites.
- Inspect git diff summary to verify Phase 1 changed the intended files.
- Record what remains deliberately deferred to Phase 2/3.

## Acceptance Criteria

- Targeted tests pass.
- Startup/docs/code consistently expose `--operational-sqlite-path`.
- No forbidden `:memory:` operational fallback exists except the explicit rejection/test.
- No factory caller can construct a registry without the SQLite path.
- Result clearly states Phase 1 delivered substrate+wiring only, not authority cutover.

## Verification Plan

- Run `pytest` for operational store and registry tests.
- Run `py_compile` for modified Cortex modules.
- Run `rg` searches for operational path wiring and fallback residue.
- Review `git diff --stat` and changed-file list.

## Risks

- Passing unit tests could hide an unconnected startup path.
- A false-positive residue search could require careful interpretation.

## Assumptions

- Phase 2 and Phase 3 remain responsible for migrating existing scope transition and active stack/status behavior.
