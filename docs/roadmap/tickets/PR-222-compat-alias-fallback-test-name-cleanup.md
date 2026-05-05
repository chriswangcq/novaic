# PR-222 Compatibility Alias / Fallback Test Naming Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Active code and test naming cleanup |
| Created | 2026-05-05 |
| Scope | `novaic-device`, `novaic-business`, shared tests |
| Dependencies | PR-141 |

## Goal

Review remaining compatibility aliases and fallback-shaped test names. Preserve
only current product semantics; delete or rename anything that exists purely to
support old callers.

## Small Tickets

### 1. Device Config Alias Review

- Objective: inspect config manager aliases and remove obsolete compatibility
  names.
- Scope: `novaic-device/device/config_agents_db.py` and callers.
- Expected result: current API names only, or aliases renamed to neutral product
  vocabulary.
- Verification: device tests and targeted `rg`.

### 2. Business Fallback Test Review

- Objective: inspect tests and code that mention owner fallback or legacy raw
  strings.
- Scope: `novaic-business/tests` and corresponding business code.
- Expected result: tests describe current behavior directly and do not preserve
  old-shape compatibility unless that is an explicit product invariant.
- Verification: business tests and targeted `rg`.

### 3. Residue Guard Update

- Objective: add or update focused guard tests for removed aliases/fallbacks.
- Scope: affected repo tests.
- Expected result: old names cannot quietly reappear.
- Verification: focused tests.

## Acceptance

- Compatibility alias/fallback naming in active code/tests is removed or
  justified as current product behavior.
- No live old caller contract remains hidden behind neutral wrappers.

## Verification

- `cd novaic-device && pytest -q`
- `cd novaic-business && pytest -q`
- targeted `rg` for `compat`, `compatibility`, `legacy`, and `fallback` in the
  affected files.

## Closure Notes

- Removed Device config manager compatibility aliases and duplicate singleton.
- Removed Business owner/device lookup fallback paths from active code.
- Reworded guard tests and comments so they describe retired surfaces directly
  instead of preserving compatibility vocabulary as if it were product behavior.
