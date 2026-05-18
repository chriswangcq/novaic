# Active stack stale injection cleanup audit

## Problem

Even if current ordering is correct, stale duplicate injection code can reintroduce confusing behavior later. Search for old active-stack collectors, file-walk stack builders, duplicated prompt fragments, and tests that preserve obsolete behavior.

## Success Criteria

- Inventory active-stack-related production and test paths.
- Classify each suspicious path as active, stale, or test-only.
- Remove stale production/test code directly if safe.
- If removal is not safe, create one focused follow-up explaining the dependency that blocks deletion.
