# P041 Result

## What Changed

- Added `LEGACY_DIRECT_REPLY_TOOL` in `ActivityTimeline.test.tsx`.
- Updated the legacy compatibility fixture to use that constant instead of free-floating direct-tool strings.
- Kept the assertion that `im_reply` is not displayed to users.

## Verification

- `npm run test:unit -- src/components/Visual/ActivityTimeline.test.tsx src/components/Visual/ActivityTimeline.acceptance.test.tsx`
  - 2 files passed, 11 tests passed.
- Focused grep leaves `im_reply` only in the explicit legacy fixture constant and the "not visible" assertion.

## Remaining Gap

Production `ActivityTimeline.tsx` legacy helper cleanup remains in `P036`.
