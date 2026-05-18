# App factory log and raw JSON detail discovery result

## Summary

Factory-log/raw-detail discovery is complete across the split children. The active Monitor timeline path is already projected and guarded, but the standalone LLM Factory Logs static page still has raw JSON/body/detail rendering that can expose long `_mcp_content` envelopes, base64/data URLs, or raw tool argument text to the browser UI. A second high-risk residue was found in the unused `SmartValue.tsx` arbitrary-value renderer; it is not an active path today, but it is exactly the kind of misleading reusable primitive that should be removed or hardened.

## Done

- Closed `P776` / `R756`: discovered the real factory logs UI in `novaic-llm-factory/static/factory-logs.html`, not `novaic-app/src`, and classified its raw/detail rendering behavior.
- Closed `P777` / `R757`: verified Monitor timeline projection/scrubbing under `novaic-app/src/components/Visual` and related hooks/types/tests.
- Closed `P778` / `R758`: discovered shared raw JSON/truncation primitives and classified the unused `SmartValue.tsx` residue.

## Verification

- `R756` shows `/v1/logs` list responses omit full request/response bodies, but `/v1/logs/{log_id}` returns bounded bodies and `factory-logs.html` still renders raw request/response JSON, message content slices, and tool-call args with simple character slicing rather than payload-aware scrubbing.
- `R757` shows Monitor timeline uses allowlisted public fields and hides debug patterns, raw payload-like details, `_mcp_content`, base64/data URL, and binary-looking content; targeted frontend tests passed for this slice.
- `R758` shows `SmartValue.tsx` recursively renders arbitrary object/string values and copies raw values with `JSON.stringify`, but usage scan found no imports outside its own module.
- No frontend/log UI files were modified in this discovery parent; only ledger and scan artifacts were added.

## Known Gaps

- Remediation candidate: add safe client-side rendering/scrubbing in `novaic-llm-factory/static/factory-logs.html` for visual message content, tool-call arguments, raw request body, and raw response body.
- Remediation candidate: remove unused `novaic-app/src/components/Visual/SmartValue.tsx`, or harden it with an explicit safe projection contract before any reuse.
- This parent is a discovery result only; implementation belongs to follow-up optimization tickets.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p776-factory-log-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p776-factory-log-evidence.txt`
- `.complex-problems/L20260516-222011/tmp/p777-monitor-timeline-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p777-monitor-timeline-evidence.txt`
- `.complex-problems/L20260516-222011/tmp/p778-json-primitives-scan.txt`
- Child result IDs: `R756`, `R757`, `R758`
