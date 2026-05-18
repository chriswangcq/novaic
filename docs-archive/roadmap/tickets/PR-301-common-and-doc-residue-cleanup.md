# PR-301 — Common And Docs Residue Cleanup

Status: Closed

## Goal

Remove no-longer-current comments, placeholders, and documentation claims that
would teach future agents the wrong active path.

## Scope

- Clean stale comments in common/runtime code where they describe removed legacy
  paths.
- Update docs/tickets touched by this cleanup with no-backcompat closure notes.
- Keep only current-path instructions in active architecture docs.

## Dependencies

- PR-297 through PR-300.

## Risks

- Over-cleaning historical docs can erase useful decision context. Prefer
  marking old compatibility as removed rather than deleting architecture history
  wholesale.

## Acceptance Criteria

- Active docs no longer present historical compatibility as current behavior.
- Code comments do not advertise removed legacy branches.
- Runtime/common tests pass.

## Verification

- Grep residue audit.
- Full runtime/common suites.

## Closure Notes

- Removed unused `WakeCondition.TIMER` and `WakeCondition.EVENT` placeholders
  from `novaic-common`.
- Removed stale legacy-removal comment residue in the common database adapter.
- Updated session harness docs/tickets so old compatibility and rollback text
  no longer reads like current behavior.
- Verified by common tests and residue grep:
  `PYTHONPATH=.:../novaic-agent-runtime pytest` in `novaic-common` -> 140
  passed.
