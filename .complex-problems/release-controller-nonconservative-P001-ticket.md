# Update source defaults for real staging releases

## Problem Definition

The source tree still leaves release-controller sample configuration and likely documentation in conservative dry-run default mode. That contradicts the requested clean operating state.

## Proposed Solution

- Change `novaic-release-controller/config.sample.json` to `dry_run_default=false`.
- Update tests that assert sample configuration behavior.
- Update release-controller architecture/runbook docs to describe default real staging execution and explicit dry-run override.
- Keep prod promotion-only language intact.

## Acceptance Criteria

- Source default is non-conservative.
- Docs no longer frame dry-run as the normal default.
- Tests and guards pass.

## Verification Plan

- Run release-controller tests.
- Run release-controller CI guard.
- Run project-level test command used for recent release-controller work.
- Review focused diff.

## Risks

- Documentation could overstate prod automation; keep prod promotion-only explicit.

## Assumptions

- Runtime activation is handled by P002.
