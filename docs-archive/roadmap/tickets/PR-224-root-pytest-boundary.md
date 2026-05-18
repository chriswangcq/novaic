# PR-224 Root Pytest Boundary Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Monorepo test boundary cleanup |
| Created | 2026-05-05 |
| Scope | Root pytest entrypoint |
| Dependencies | PR-219..PR-223 |

## Goal

Make `pytest` from the monorepo root a deterministic root guard check instead
of an accidental recursive collection across submodules, vendored code, app
artifacts, and repos with incompatible import roots.

## Small Tickets

### 1. Root Collection Boundary

- Objective: define what root `pytest` owns.
- Scope: root pytest config.
- Expected result: root `pytest` only runs root-level CI guard tests.
- Verification: `pytest -q` from the repository root.

### 2. Obsolete Root Test Removal

- Objective: remove the stale root `test_skills.py` file that imported retired
  Gateway internals.
- Scope: root test files.
- Expected result: no root test depends on old Gateway APIs or subrepo import
  paths.
- Verification: `pytest -q` from the repository root.

### 3. Python Test Artifact Hygiene

- Objective: keep root test execution from leaving generated Python cache files
  in the working tree.
- Scope: root ignore rules.
- Expected result: running root pytest does not create visible untracked
  `__pycache__` or `.pyc` artifacts.
- Verification: `pytest -q` followed by `git status --short`.

## Acceptance

- Running `pytest -q` from the root is valid and deterministic.
- Subrepo tests remain owned by each subrepo's own test command.
- Root test collection no longer scans submodules, vendor trees, generated app
  assets, or stale ad-hoc root tests.
- Root test execution leaves the working tree free of generated Python cache
  artifacts.

## Verification

- `pytest -q`
