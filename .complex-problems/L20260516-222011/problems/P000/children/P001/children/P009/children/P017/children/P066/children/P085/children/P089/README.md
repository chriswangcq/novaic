# App non-monitor final residue scan and guard verification

## Problem

After classifying non-monitor App residue slices, the final App scan must ensure no unclassified active fallback/compatibility/direct-tool/base64 residue remains and existing guard tests still reflect the current contract.

## Success Criteria

- Re-run bounded `novaic-app/src` residue scans after child cleanup/classification.
- Confirm remaining hits are classified current behavior, product vocabulary, or tests/guards.
- Run focused App test commands covering touched and guard files.
- Record a final residual-risk statement for the non-monitor App scope.
