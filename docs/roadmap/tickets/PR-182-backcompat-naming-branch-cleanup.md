# PR-182 — Back-compat naming and branch cleanup

Status: `[closed]` — 2026-05-03

## Goal

Remove confirmed stale compatibility names, comments, and helper branches that now mislead maintainers. Keep only active concepts with active owners.

## Required Process

1. Analyze remaining `legacy`, `compat`, `backcompat`, and retired-path references in active code.
2. Create small implementation tickets for each safe deletion or rename.
3. Delete stale branches/comments/import aliases and add guards where useful.
4. Confirm closure with tests, smoke, deploy if runtime code changed, and git commit.

## Tests

- Focused tests around touched modules.
- Static guard scans for deleted concepts.
- Full suite for affected subrepo when behavior changes.

## Deployment / Git

- Deploy only if active runtime code changes.
- Commit/push each independently mergeable change.

## Small Tickets

- [PR-182A](PR-182A-delete-legacy-business-health-stubs.md) — closed. Removed retired Business health stubs and `stuck_sending_timeout` config shape from shared/packaged configs.
- [PR-182B](PR-182B-remove-cortex-compat-helpers.md) — closed. Removed unused Cortex compatibility helpers and old naming.

## Closure

PR-182 is closed by PR-182A and PR-182B. The remaining occurrences of retired names are tests/guardrails or historical ticket notes that explicitly say the old helper/path has been deleted.
