# Classify low-density boundary test residue hits

## Problem

Classify the remaining low-density test residue hits not owned by the high-density lifecycle/recovery or cutover/guardrail groups. This group prevents many one-off test hits from being hand-waved as harmless.

Initial file group:
- All files in `.complex-problems/L20260516-222011/tmp/p531/static-residue-tests.txt` that are not listed in the two high-density child groups.

## Success Criteria

- Remaining test hit count and file count are recorded.
- Every remaining test file gets a purpose/category rationale, even if it has only one hit.
- Stale or misleading one-off tests become follow-up.
- This group does not double-count files assigned to the high-density child groups.
