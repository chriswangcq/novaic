# Make source defaults and docs non-conservative

## Problem

The repository still presents the release-controller as dry-run by default in sample config or documentation. This creates drift from the desired clean operating model where staging branch releases execute for real unless explicitly requested as dry-run.

## Success Criteria

- `novaic-release-controller/config.sample.json` has `dry_run_default=false`.
- Tests expecting the sample config are updated.
- Documentation describes non-dry-run default staging execution and keeps prod promotion-only.
- Relevant tests and guards pass.
