# Add release-controller tests and CI guards

## Problem

The new release-controller path must be protected against ambiguous branch rules, mutable image tags, unsafe prod auto-deploy, missing dry-run, and stale GitHub-Actions-primary documentation.

## Success Criteria

- Tests and guards run locally without external services.
- Guard rejects prod auto-deploy from ordinary branch polling.
- Guard requires immutable refs/digests for prod promotion.
- Guard verifies controller docs are primary and GitHub Actions is secondary.
- Existing relevant tests/guards still pass.

