# T001 Result: Source defaults made non-conservative

## Summary

Updated release-controller source defaults and documentation so normal branch-triggered staging releases are non-dry-run by default, while explicit dry-run remains available for observation and prod remains promotion-only.

## Done

- Changed `ControllerConfig.dry_run_default` default from `true` to `false`.
- Changed `novaic-release-controller/config.sample.json` to `"dry_run_default": false`.
- Added test coverage that missing `dry_run_default` is non-conservative.
- Updated release-controller architecture docs:
  - current/target runtime policy now says `dry_run_default=false`.
  - operators use explicit `dry_run=true` only when intentionally observing/planning.
  - migration plan now includes real staging execution and release submodule allowlist.
- Updated deploy runbook:
  - omitted `dry_run` means runtime default execution.
  - current autonomous polling state is `dry_run_default=false`.
  - prod guard remains promotion/rollback API only.

## Verification

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`: 36 passed.
- `python3 -m pytest -q scripts/ci/test_release_controller_ci.py`: 6 passed.
- `python3 -m pytest -q`: 11 passed.
- `bash -n deploy`: passed.
- Search found no remaining `dry_run_default=true` or stale current-limit wording in release-controller docs/config.

## Known Gaps

- Runtime API-host config is handled by P002.

## Artifacts

- `novaic-release-controller/release_controller/models.py`
- `novaic-release-controller/config.sample.json`
- `novaic-release-controller/tests/test_config_models.py`
- `docs/architecture/release-controller.md`
- `docs/runbooks/deploy.md`
