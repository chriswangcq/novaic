# Rewrite Path Normalization and Abuse Root Scratch Fixtures

## Problem Definition

Path normalization and abuse tests still contain `/rw/scratch` in positive and negative paths. These tests should continue proving traversal rejection, double-slash normalization, unicode/control path handling, and runtime path validation without canonizing root scratch.

## Proposed Solution

Replace `/rw/scratch` in path adversarial/runtime path abuse tests with neutral `/rw/tmp` paths while preserving each test's exact assertion. For tests that intentionally compare normalized aliases, update both sides consistently.

## Acceptance Criteria

- Target path-abuse tests no longer use root `/rw/scratch` unless explicitly justified as an adversarial string.
- Traversal rejection, double-slash normalization, unicode/control path handling, and runtime path validation tests still pass.
- Focused path tests pass.

## Verification Plan

Run scans for `/rw/scratch` in `test_paths_adversarial.py`, `test_runtime_path_abuse.py`, and `test_workspace_paths.py`; run focused tests for those files.

## Risks

- Updating one side of a normalization assertion but not the other can weaken the test.
- Negative traversal paths must remain malicious enough to exercise validation.

## Assumptions

- `/rw/tmp` is a neutral arbitrary RW path for path validation tests.
