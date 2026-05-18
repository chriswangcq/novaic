# Frontend timeline preview audit result

## Summary

Audited the frontend Agent Monitor timeline/list preview path. The normal collapsed timeline preview is React-rendered, escaped by default, and bounded with `DETAIL_PREVIEW_LIMIT = 84`; hook normalization uses an allowlist so debug fields like `_mcp_content` and `result_id` are not copied into timeline records. Focused ActivityTimeline tests pass.

## Done

- Scanned `novaic-app/src` for Agent Monitor, activity timeline, preview, truncation, base64/image, debug field, and artifact terms.
- Captured exact slices for:
  - `ActivityTimeline.tsx` public title/detail projection and preview limit.
  - `ActivityTimeline.tsx` row rendering for collapsed/expanded details.
  - `useActivityTimeline.ts` record allowlist normalization and max-record slicing.
  - ActivityTimeline tests and guard tests.
- Ran focused frontend tests using the actual script `npm run test:unit`.

## Verification

- Artifact: `.complex-problems/L20260516-222011/tmp/p606-timeline-preview-evidence.txt`.
- Test artifact: `.complex-problems/L20260516-222011/tmp/p606-activity-timeline-tests.txt`.
- Correct focused test run passed:
  - `Test Files 4 passed (4)`
  - `Tests 17 passed (17)`
- Initial `npm test` command failed because `novaic-app/package.json` has no `test` script; the correct script is `test:unit`.

## Known Gaps

- Collapsed timeline preview is bounded, but expanded inline details can show the full `record.text` if upstream sends a long non-debug string. This is probably covered by the parent split child for detail/raw JSON boundaries, but it is a real dependency on backend bounded text for normal timeline data.
- No explicit frontend base64 detector exists in `ActivityTimeline.tsx`; protection comes from backend bounded monitor records, React escaping, preview slicing, and debug-field filtering.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p606-timeline-preview-evidence.txt`
- `.complex-problems/L20260516-222011/tmp/p606-activity-timeline-tests.txt`
