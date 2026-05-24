# P004 Result

## Summary

Added repository-level CI guards for release-controller tests, packaging, Compose, and deploy invariants.

## Done

- Added `scripts/ci/test_release_controller_ci.py`.
- Guard runs the release-controller unit suite.
- Guard checks Dockerfile invariants.
- Guard checks Compose invariants and renders Compose when `docker-compose` is available.
- Guard verifies deploy help/path markers and mutable-ref rejection.
- Guard verifies it is registered in `scripts/run_all_tests.sh` and `.github/workflows/lint.yml`.
- Added the guard to `scripts/run_all_tests.sh`.
- Added the guard to `.github/workflows/lint.yml`.

## Verification

- `python3 -m pytest -q scripts/ci/test_release_controller_ci.py`
  - Passed: 6 tests.
- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: 31 tests.
- `python3 -m pytest -q`
  - Passed: 11 root CI tests.

## Known Gaps

- This guard does not require Docker daemon access. Real image build remains covered by deployment/CI environment validation.

## Artifacts

- `scripts/ci/test_release_controller_ci.py`
- `scripts/run_all_tests.sh`
- `.github/workflows/lint.yml`
