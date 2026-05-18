# PR-230 — App One-off Patch Script Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | App maintenance cleanup |
| Created | 2026-05-05 |
| Scope | tracked App one-off patch scripts |
| Dependencies | PR-225 |

## Goal

Remove tracked one-off UI patch scripts that were useful during historical
refactors but now only increase maintenance entropy.

## Small Tickets

### PR-230A — Delete One-off UI Patch Scripts

- Objective: remove historical patch scripts that mutate App source via ad hoc
  string replacement.
- Scope: `novaic-app/patch_*.py`, `novaic-app/update_handover_settings.py`.
- Expected result: tracked App source no longer includes one-off codegen/patch
  scripts.
- Verification: targeted `rg` and App status check.

### PR-230B — Preserve Product Migration Script Decision

- Objective: decide whether `scripts/migrate-avd-to-data-dir.sh` is product
  migration or dead one-off.
- Scope: App scripts and docs references.
- Expected result: keep only if it is a product/user data migration entrypoint;
  otherwise remove.
- Verification: targeted `rg`.

## Acceptance

- Historical UI patch scripts are physically deleted.
- Any remaining App script has a current product purpose.
- App tests/build do not depend on deleted scripts.

## Closure

Closed 2026-05-05. Tracked one-off UI patch scripts and the unreferenced AVD
data-dir migration script were physically deleted.
