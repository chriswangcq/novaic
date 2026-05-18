# Repository Scripts Residue Scan

## Problem

Top-level and package-level repository scripts may contain stale compatibility, fallback, migration, or historical policy wording.

## Success Criteria

- Scan `scripts/` and shell/python script files outside test directories for residue markers.
- Classify hits as active policy, harmless script text, or stale residue.
- Remove safe stale residue.
- Run representative script or lint verification.
