# Audit Scope Transition Call Sites

## Problem Definition

Phase 2 migration needs a precise map of current scope transition writers/readers and test expectations before modifying lifecycle code.

## Proposed Solution

Inspect `scope_state.py`, `scope_state_log.py`, `workspace.py`, `/v1/scope/history`, and related tests. Record:

- writer call sites
- reader call sites
- current NDJSON record shape
- target SQLite event shape
- test files that must change
- cleanup decision for the old NDJSON module/path

## Acceptance Criteria

- Concrete file/function pointers are listed.
- SQLite event mapping is explicit.
- Test impact is listed.
- Cleanup stance is clear.

## Verification Plan

- Use `rg` and focused file reads.
- Record evidence in the result body.

## Risks

- Missing one writer can leave dual truth.

## Assumptions

- No code changes are made in this audit child.
