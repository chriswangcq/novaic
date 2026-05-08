# CI Bytecode And Generated Artifact Hygiene

## Problem

Python lints/tests can generate `__pycache__`, causing generated-artifacts lint to fail when commands are chained. Standardize guard invocation or cleanup so generated artifact checks are stable.

## Success Criteria

- CI guard scripts or documented command wrappers use `PYTHONDONTWRITEBYTECODE=1` where appropriate.
- Generated-artifact lint passes after the normal guard sequence.
- Any generated cache artifacts from local verification are cleaned.

