# Remove dry_run_default from source contract

## Problem

Active release-controller code, tests, sample config, and docs still expose `dry_run_default`. Remove this global switch so the only dry-run behavior is an explicit request field.

## Success Criteria

- `ControllerConfig` has no `dry_run_default` field, parsing, validation, or serialized output.
- `ReleasePlanner` resolves omitted `dry_run` to execution and explicit `dry_run=true` to simulation.
- Sample config and docs describe the clean contract without global dry-run defaults.
- Tests cover omitted `dry_run` executing by default and explicit dry-run still skipping command execution.
- `rg dry_run_default` returns no matches in active release-controller/docs/deploy/CI paths after this child is complete.
