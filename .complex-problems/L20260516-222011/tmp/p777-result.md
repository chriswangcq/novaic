# App monitor timeline payload projection discovery result

## Summary

Agent Monitor timeline/detail rendering was discovered and inspected. The production timeline path is already a public projection surface: it normalizes records onto an allowlist, suppresses debug fields, hides JSON-like/debug text, detects data URL and base64-like raw payload text, and renders a placeholder instead of raw media payloads. Relevant guard and behavior tests exist and passed. No monitor/timeline remediation candidate was found.

## Done

- Discovered Monitor/timeline components, hooks, types, entity contracts, and tests under `novaic-app/src`.
- Inspected `ActivityTimeline`, `useActivityTimeline`, ActivityTimeline guard/acceptance tests, and behavior tests for raw payload exposure.
- Classified `_mcp_content`, debug IDs, base64/data URL, BlobRef, artifact, truncation, and projection helper hits.
- Ran targeted frontend tests for the Monitor timeline projection path.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p777-monitor-timeline-scan.txt`.
- Evidence artifact: `.complex-problems/L20260516-222011/tmp/p777-monitor-timeline-evidence.txt`.
- `novaic-app/src/components/hooks/useActivityTimeline.ts` normalizes records onto explicit public fields only: order, phase, kind, title, text, truncated, tool, status, and has_payload.
- `novaic-app/src/components/Visual/ActivityTimeline.tsx` hides debug patterns including `result_id`, `_mcp_content`, `/ro/active`, gateway errors, stack traces, JSON-like details, action tool text, and bookkeeping tool rows.
- `ActivityTimeline.tsx` detects raw image data URLs and long base64-like payloads and replaces them with `输出包含较大的原始文件数据，已在监控中隐藏。`.
- `ActivityTimeline.guard.test.ts` asserts the production component and hook do not contain raw diagnostic rendering vocabulary or broad object spreading.
- `ActivityTimeline.acceptance.test.tsx` asserts normal monitor output does not expose `Execution Result`, `result_id`, `_mcp_content`, or raw `agentctl im reply` text.
- `ActivityTimeline.test.tsx` covers hiding image data URLs, JPEG-like base64 payload text, debug-only fields, raw transport errors, and floating-layer debug fields.
- `useActivityTimeline.test.ts` verifies normalization drops `step_ref`, `_mcp_content`, `wake_triggers`, and other non-public fields.
- Targeted tests passed: `npm run test:unit -- ActivityTimeline.guard.test.ts ActivityTimeline.test.tsx ActivityTimeline.acceptance.test.tsx useActivityTimeline.test.ts` in `novaic-app` (4 files, 19 tests).

## Known Gaps

- No remediation candidate in the Monitor/timeline projection slice.
- This child does not cover Factory Logs raw JSON UI; that is handled separately by P776.
- No monitor/timeline UI files were modified.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p777-monitor-timeline-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p777-monitor-timeline-evidence.txt`
