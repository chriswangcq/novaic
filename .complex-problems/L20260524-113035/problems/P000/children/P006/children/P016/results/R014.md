# P016 Result

## Summary

Updated release-controller CI/CD documentation to reflect the implemented and deployed self-hosted control-plane path.

## Done

- Updated `docs/architecture/release-controller.md`.
- Updated `docs/runbooks/deploy.md`.
- Documented current API host deployment:
  - container name
  - digest image
  - loopback bind
  - config/state/compose paths
- Documented health/status checks.
- Documented `./deploy release-controller-image <image-ref>`.
- Documented dry-run default and managed worktree requirement before real non-dry-run branch releases.
- Reframed GitHub Actions as fallback/secondary verification rather than long-term release orchestrator.
- Documented that the controller has no public Nginx route.

## Verification

- `rg -n "Current Deployment|127\\.0\\.0\\.1:19880|release-controller-image|dry_run_default=true|managed git worktree|no public Nginx|secondary verification/fallback|GitHub Actions fallback" docs/architecture/release-controller.md docs/runbooks/deploy.md`
  - Found required markers.
- `python3 -m pytest -q scripts/ci/test_release_controller_ci.py`
  - Passed: 6 tests.

## Known Gaps

- Docs accurately state that managed worktree setup remains before enabling real non-dry-run branch execution.

## Artifacts

- `docs/architecture/release-controller.md`
- `docs/runbooks/deploy.md`
