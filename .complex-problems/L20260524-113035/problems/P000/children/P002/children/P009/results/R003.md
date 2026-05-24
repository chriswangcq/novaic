# P009 Result

## Summary

Implemented release-controller branch planning and command runner modules.

## Changes

- Added `release_controller.planner`.
- Added `ReleasePlanner` for branch rule matching, namespace resolution, branch release planning, prod promotion planning, and rollback planning.
- Added strict immutable image ref validation for digest refs and `sha-<hex>` tags.
- Added branch automation guard so branch-triggered releases cannot target `prod`.
- Added deterministic command plans using existing deploy commands:
  - `./deploy services-image <namespace> <api-image-ref>`
  - `./deploy factory-image <namespace> <factory-image-ref>`
- Added `release_controller.runner.CommandRunner`.
- Added dry-run runner behavior that records skipped commands without execution.
- Added subprocess execution behavior that captures stdout, stderr, exit code, and stops after first failure.
- Added `CommandResult` model.
- Exported planner and runner types from the package.
- Added planner/runner unit tests.

## Verification

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: 19 tests.
- `PYTHONPATH=novaic-release-controller python3 - <<'PY' ...`
  - Confirmed package import, sample config load, state store creation, and branch rule matching.

## Notes

- Initial rollback test used an intentionally invalid-looking fake ref (`sha-commit-1`); strict validation rejected it. The test data was corrected to valid `sha-<hex>` refs instead of weakening image ref rules.
- This slice does not implement HTTP endpoints or a background polling loop. Those remain assigned to later child problems.
