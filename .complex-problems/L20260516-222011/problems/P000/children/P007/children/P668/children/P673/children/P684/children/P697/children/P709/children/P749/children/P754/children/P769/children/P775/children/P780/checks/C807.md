# P780 success check

## Summary

Success. `R761` satisfies the Monitor shell-artifact projection discovery scope with direct source evidence and focused tests. Unlike Chat and factory logs, this slice did not reveal an additional remediation candidate.

## Evidence

- `R761` records the scan artifact `.complex-problems/L20260516-222011/tmp/p780-monitor-shell-artifact-scan.txt`.
- `useActivityTimeline.ts` allowlists activity record fields and drops unknown payload data.
- `ActivityTimeline.tsx` suppresses raw action tool details and hides raw payload-like text, including `_mcp_content`, `data:image` base64, long base64 strings, binary prefixes, and debug/transport detail patterns.
- Focused tests passed for ActivityTimeline guard, behavior, acceptance, and hook normalization.

## Criteria Map

- Monitor, ActivityTimeline, activity hook/type, and guard test files are discovered: satisfied.
- Hits for shell actions, tool output details, `tool-output.v1`, artifacts, Blob refs, truncation, raw payload hiding, and display/media preview are classified: satisfied; shell/detail/payload hiding behavior is explicit, while no `tool-output.v1` parser exists in this slice.
- Exact remediation candidates are listed, or absence is explicitly recorded: satisfied; no Monitor-specific remediation candidate was found.
- No Monitor UI files are modified: satisfied; only ledger/tmp artifacts were added.

## Execution Map

- `T772` was one-go after the parent split narrowed the scope to Monitor/ActivityTimeline.
- Execution scanned source, inspected high-signal files, and ran targeted tests.
- Result `R761` records no additional Monitor-specific defect.

## Stress Test

- Could raw artifact JSON be exposed through unknown fields? `normalizeActivityRecord` drops unknown fields before UI rendering.
- Could raw payload text be expanded by the user? `publicFullDetail` blocks JSON-like braces and binary/base64-like strings before expansion.
- Could shell action commands leak through action records? `publicFullDetail` suppresses action records with a tool.
- Could tests be stale? The tests directly assert hiding `_mcp_content`, data URLs, long base64, raw transport errors, and payload refs, which matches the discovered risk class.

## Residual Risk

None specific to Monitor shell artifact projection. Broader app raw JSON and legacy Chat residue are tracked by sibling/parent findings.

## Result IDs

- `R761`
