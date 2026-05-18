# PR-227 — Ignored Generated Artifact Hygiene

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Workspace hygiene |
| Created | 2026-05-05 |
| Scope | ignored Python/test generated files in source and packaged resource trees |
| Dependencies | PR-225 |

## Goal

Clean ignored generated artifacts that can mislead grep, packaging, or source
review, then add a narrow guard for source/resource areas that must stay free of
generated caches.

## Small Tickets

### PR-227A — Physical Generated Artifact Cleanup

- Objective: remove ignored `__pycache__`, `.pyc`, `.pytest_cache`, and
  `*.egg-info` artifacts from active source and packaged resource trees.
- Scope: root repo and submodules.
- Expected result: no such generated artifacts remain in active source/resource
  directories.
- Verification: targeted `find`.

### PR-227B — Source/Resource Hygiene Guard

- Objective: add a lightweight guard that fails if generated artifacts reappear
  in active source or packaged resource trees.
- Scope: root `scripts/ci`.

## Closure

Closed 2026-05-05. Ignored generated Python/test artifacts were removed from
active source/resource areas, and `scripts/ci/lint_generated_artifacts.sh`
guards those areas against reintroducing caches or egg metadata.
- Expected result: future packaging/source scans are not polluted by generated
  cache files.
- Verification: run the guard.

## Acceptance

- Targeted generated-artifact scan returns no active source/resource hits.
- The new guard passes.
- Third-party/vendor caches are not treated as product source unless they are in
  packaged App resources.
