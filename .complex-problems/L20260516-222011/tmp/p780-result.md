# App monitor shell artifact projection discovery result

## Summary

Monitor / ActivityTimeline shell-artifact projection is contract-compliant in the inspected active path. It normalizes incoming activity rows to an allowlisted `ActivityTimelineRecord`, projects public titles/details, hides action tool details, hides raw payload-like data including `_mcp_content`, `data:image` base64, and long binary-looking base64, and relies on `has_payload` as a compact saved-result hint. Focused ActivityTimeline tests pass. No Monitor-specific remediation candidate was found.

## Done

- Scanned Monitor/ActivityTimeline components, hooks, types, and tests for shell/artifact/media/raw-payload terms.
- Inspected `ActivityTimeline.tsx`, `useActivityTimeline.ts`, and test coverage around shell details, display/base64 hiding, `_mcp_content`, transport errors, and payload refs.
- Ran focused ActivityTimeline/useActivityTimeline unit tests.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p780-monitor-shell-artifact-scan.txt`.
- `useActivityTimeline.ts` normalizes records to explicit fields: `order`, `phase`, `kind`, `title`, `text`, `truncated`, `tool`, `status`, and `has_payload`; unknown payload fields are dropped.
- `ActivityTimeline.tsx` hides action tool details, skill bookkeeping, debug-detail patterns, raw JSON-like braces, `_mcp_content`, `/ro/active`, gateway error/stack trace details, `data:image` base64, long base64-like payloads, and binary prefixes.
- `ActivityTimeline.tsx` maps `has_payload` without text to `结果已保存，需要时可以继续查看细节`, which fits the shell terminal-text plus payload-reference contract.
- Focused tests passed: `cd novaic-app && npm run test:unit -- ActivityTimeline.guard.test.ts ActivityTimeline.test.tsx ActivityTimeline.acceptance.test.tsx useActivityTimeline.test.ts` => 4 files, 19 tests passed.

## Known Gaps

- No Monitor-specific remediation candidate in this shell artifact projection slice.
- Factory Logs raw JSON and unused generic `SmartValue.tsx` are separate parent findings, not Monitor-specific defects.
- No Monitor UI files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p780-monitor-shell-artifact-scan.txt`
- Focused ActivityTimeline test output from `novaic-app`.
