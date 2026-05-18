# Targeted guard patch implementation

## Problem

If the gap matrix finds concrete missing or stale guard coverage, implement the smallest targeted guard changes. If no concrete gap exists, record a no-change result with evidence rather than inventing noisy guards.

## Success Criteria

- Patches concrete guard gaps found by the matrix, if any.
- Does not add broad bans that would catch valid lower-layer generic code/tests/docs.
- Records changed files or explicit no-change rationale.
