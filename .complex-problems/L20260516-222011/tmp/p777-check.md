# App monitor timeline payload projection discovery check

## Summary

Success. R757 satisfies the Monitor/timeline discovery criteria with bounded source evidence and targeted tests. The one-go path is acceptable because the surface is narrow, no files were modified, and the result proves both source-level allowlisting and runtime behavior tests.

## Evidence

- R757 cites the source scan and evidence artifacts for Monitor/timeline code.
- `useActivityTimeline.ts` uses explicit public-field normalization rather than spreading raw records.
- `ActivityTimeline.tsx` filters debug details, JSON-like details, action tool details, bookkeeping rows, and raw binary/media-looking payload text.
- Guard, acceptance, component, and hook tests all exist and passed in the targeted test run.

## Criteria Map

- Monitor/timeline files and tests discovered: satisfied by the scan artifact and R757 file list.
- Hits for `_mcp_content`, tool output, display results, base64/data URLs, BlobRefs, artifacts, truncation, and projection helpers classified: satisfied by R757 Verification.
- Exact remediation candidates listed, or absence recorded: satisfied; R757 records no remediation candidate in this slice.
- No monitor/timeline UI files modified: satisfied.

## Execution Map

- T768 was classified as one-go, executed as bounded source/test discovery, and recorded as R757.
- Targeted tests were run in `novaic-app` and passed: 4 files, 19 tests.
- Factory Logs and shared raw JSON primitives remain separate child problems, so this check does not hide broader raw JSON risk.

## Stress Test

- Plausible failure mode: raw base64 or `_mcp_content` could enter through backend records even if TypeScript types are clean. The component tests explicitly pass hostile data URL, JPEG-like base64, `_mcp_content`, `result_id`, and transport error values and assert they are not rendered.
- Plausible failure mode: hook normalization could spread raw backend entities. The guard and hook tests assert no `...item` and no raw diagnostic fields survive normalization.

## Residual Risk

- Non-blocking: ActivityTimeline intentionally hides JSON-like details; if future product needs structured-but-safe detail rendering, that should be a new design ticket rather than a payload leak fix.
- Non-blocking: this child did not inspect Factory Logs or shared SmartValue behavior outside Monitor.

## Result IDs

- R757
