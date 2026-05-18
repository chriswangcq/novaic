# Tests Stale Contract Audit

## Problem

Search tests for old contracts, old paths, compatibility assertions, or test helpers that preserve stale behavior instead of current architecture.

## Success Criteria

- Runs focused scans over tests for old path/tool/compatibility terms.
- Inspects high-risk hits in Cortex/runtime/common/business where contract drift matters.
- Rewrites or deletes tests that only protect stale behavior.
- Runs affected test files after any changes.
