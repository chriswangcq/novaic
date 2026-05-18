# Implement Device screenshot route disposition

## Summary

Apply the route disposition chosen by the usage analysis, with focused tests.

## Problem

After route usage is known, the code must stop leaving this route as ambiguous media-byte residue.

## Success Criteria

- If removable, delete the route and update tests/docs.
- If still needed, convert or explicitly mark it legacy/debug-only according to the analysis result.
- Focused tests pass.
- Follow-up is spawned if external compatibility cannot be resolved in-repo.
