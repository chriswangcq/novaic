# Validate and publish controller-only release commit

## Problem

The repository has controller-only release changes that must be validated and published carefully. The code must be committed without unrelated dirty files, and the local test matrix should pass before pushing a commit that remote Release Controller will consume.

## Success Criteria

- Full relevant local test matrix passes, including release-controller tests and repository guard/lint matrix.
- Git diff is reviewed so unrelated dirty files are not staged.
- Controller-only changes are committed and pushed to `main`.
- Remote polling is paused before push or otherwise prevented from running the guarded deploy with the old controller image.
