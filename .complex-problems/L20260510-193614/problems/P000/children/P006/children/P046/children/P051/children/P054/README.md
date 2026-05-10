# Phase 5B3.3 Legacy Test And Comment Wording Cleanup

## Problem

Some live tests and comments use `legacy` or migration wording even when they now describe current explicit contracts or guard behavior. This makes residue harder to audit and can encourage future compatibility paths.

## Success Criteria

- Rename tests whose `legacy` wording refers to current explicit behavior rather than historical guard scenarios.
- Preserve tests that intentionally prove old legacy behavior is removed, but make their purpose explicit.
- Clean stale compatibility/legacy comments in live source where they are not documenting a current migration or removal guard.
- Do not touch historical design/review docs; Phase 5C owns current documentation/comment sweep beyond this source/test cleanup.
- Targeted context-event no-compat and projection tests pass.
