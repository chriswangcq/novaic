# P004 Check - Docs Status Consistency Lint

## Summary

P004 is solved. The known stale PR-338 docs status is corrected, and CI now has a narrow status-consistency lint to prevent that drift from returning.

## Evidence

- PR-338 ticket now says `Status: Closed`.
- PR-338 ticket now says `P007 closed`.
- `scripts/ci/lint_docs_status_consistency.py` checks the PR-338 ticket and architecture plan markers.
- `.github/workflows/lint.yml` runs the new lint.
- Local docs lints pass.

## Criteria Map

- Architecture/roadmap status mismatches are detected by tooling -> satisfied.
- Known PR-338 stale status is fixed -> satisfied.
- Lint passes locally -> satisfied.
- Existing docs lints still pass -> satisfied.

## Execution Map

- T017 -> R016: docs fix, CI lint, verification.

## Stress Test

- Reintroducing `Status: Doing` or `P007 in progress` to PR-338 would fail the new lint.
- Removing the closed phase 13 marker from the architecture plan would fail the new lint.

## Residual Risk

- The first lint version is intentionally narrow. Future status-contracts should be added as explicit expectations when new architecture docs become SSOT.

## Result IDs

- R016

## Blocking Gaps

- none
