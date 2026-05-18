# App test residue scan

## Problem

`novaic-app/src` tests may contain stale skip/TODO/FIXME/compat/fallback/legacy/base64 fixtures that preserve old frontend behavior.

## Success Criteria

- Scan App tests for skip/xfail/TODO/FIXME/compat/fallback/legacy/base64/direct-tool markers.
- Classify hits as intentional guard, harmless fixture text, current product vocabulary, or stale residue.
- Clean tiny stale test residue when safe.
- Run focused App tests or explicit no-code-change verification.
