# CI and Lint Helper Residue Scan

## Problem

CI workflow files and lint/test helper scripts may contain stale compatibility, fallback, migration, or historical policy wording that no longer matches the final architecture.

## Success Criteria

- Scan `.github/`, CI config, and lint/test helper files for residue markers.
- Classify hits as active guard/policy, harmless fixture text, or stale residue.
- Remove safe stale residue.
- Run relevant lint/helper checks or explicit no-code-change verification.
