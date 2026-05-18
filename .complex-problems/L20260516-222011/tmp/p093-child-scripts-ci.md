# Scripts and CI Helper Residue Scan

## Problem

Repository scripts, CI helpers, and shell lint/test scripts may contain stale compatibility, fallback, migration, or policy wording that no longer matches the final runtime/tool contract.

## Success Criteria

- Scan scripts and CI/test helper paths for residue markers.
- Classify hits as active policy/guard wording, harmless fixture text, or stale residue.
- Remove safe stale wording when found.
- Run relevant script/lint checks or record explicit no-code-change verification.
