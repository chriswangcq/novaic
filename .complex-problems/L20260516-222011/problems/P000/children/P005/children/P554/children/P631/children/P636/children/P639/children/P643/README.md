# Path Normalization and Abuse RW Fixture Rewrite

## Problem

Path normalization/adversarial tests include `/rw/scratch` in positive and negative path strings. These should be rewritten carefully so they still test normalization and traversal rejection without canonizing root scratch.

## Success Criteria

- Updates `test_paths_adversarial.py`, `test_runtime_path_abuse.py`, and any related path tests.
- Preserves traversal rejection, double-slash normalization, unicode/control/path abuse checks, and runtime path validation semantics.
- Runs focused path abuse tests.
