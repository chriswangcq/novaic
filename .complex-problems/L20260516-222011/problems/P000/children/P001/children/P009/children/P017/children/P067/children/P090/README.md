# Runtime queue test residue scan

## Problem

`novaic-agent-runtime/tests` may contain stale skip/TODO/FIXME/compat/fallback/legacy fixtures that keep deprecated queue/FSM/session behavior acceptable.

## Success Criteria

- Scan runtime tests for skip/xfail/TODO/FIXME/compat/fallback/legacy/direct-tool/base64 markers.
- Classify hits as intentional guard, harmless fixture text, or stale acceptance.
- Clean tiny stale test residue when safe.
- Run focused runtime tests or explicit no-code-change verification.
