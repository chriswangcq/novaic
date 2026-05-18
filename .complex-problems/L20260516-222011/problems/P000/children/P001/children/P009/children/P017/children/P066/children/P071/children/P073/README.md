# App monitor UI fallback compatibility residue scan

## Problem

App monitor/UI code and tests may still normalize old direct tool names or contain legacy/fallback wording that is no longer part of the final shell-first architecture.

## Success Criteria

- Focused scans cover `novaic-app/src` for legacy, fallback, compat, TODO/FIXME, direct tool names, and shell/display wording.
- Hits are classified as active UI behavior, test fixture, localization/product text, or stale residue.
- Safe tiny cleanup is applied directly if found.
- Focused frontend tests/lint pass for touched files.
