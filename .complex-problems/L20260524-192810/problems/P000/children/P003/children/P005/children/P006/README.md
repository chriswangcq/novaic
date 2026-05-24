# Make Release Controller image capable of running quality gates

## Problem

The default `quality_gates` include pytest-based controller CI checks, but the Release Controller Docker image currently installs only the release-controller package and runtime tooling. Without pytest in the image, the API-host controller cannot execute the default gate list and staging admission would fail for an infrastructure reason rather than a code quality reason.

## Success Criteria

- Release Controller Docker image installs the minimal test tooling required by default `quality_gates`.
- Dockerfile invariant tests cover that the test tooling remains available.
- Sample quality gates remain executable inside the controller worktree.
- Local tests for release-controller and release-controller CI guards pass after the image change.
