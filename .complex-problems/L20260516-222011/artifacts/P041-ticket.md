# Ticket: classify app monitor test direct-tool fixtures

## Problem Definition

App monitor tests intentionally cover old direct IM records for legacy display compatibility, but the literal fixture names should be clearly marked as legacy data.

## Proposed Solution

- Introduce explicit legacy fixture constants in `ActivityTimeline.test.tsx`.
- Keep the compatibility test, but make the raw direct-tool tokens flow through legacy-named constants.
- Leave production component legacy-boundary cleanup to `P036`.

## Acceptance Criteria

- App tests do not present direct IM records as current behavior.
- Legacy direct IM fixtures are explicitly named.
- Focused ActivityTimeline tests pass.

## Verification Plan

- Focused `rg` over ActivityTimeline tests.
- Run focused ActivityTimeline frontend tests.

## Risk

Do not remove the compatibility assertion that old archived records still display friendly user-facing text.
