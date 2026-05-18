# Path Normalization and Abuse RW Fixture Rewrite Result

## Summary

Rewrote path normalization and abuse tests from root `/rw/scratch` to neutral `/rw/tmp` while preserving traversal rejection, double-slash normalization, unicode path roundtrip, runtime prefix validation, and workspace path validation behavior.

## Changes

- `tests/test_paths_adversarial.py`: updated positive and negative RW path fixtures to `/rw/tmp`.
- `tests/test_runtime_path_abuse.py`: updated rejected relative paths and accepted RW prefix example to `/rw/tmp`.
- `tests/test_workspace_paths.py`: updated traversal write fixture to `/rw/active/../tmp/nope.txt`.

## Verification

- `.complex-problems/L20260516-222011/tmp/p643-scan.txt` shows no root `/rw/scratch` or `rw/scratch` remains in targeted path test files.
- `.complex-problems/L20260516-222011/tmp/p643-tests.txt` shows 47 focused tests passed.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p643-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p643-tests.txt`
