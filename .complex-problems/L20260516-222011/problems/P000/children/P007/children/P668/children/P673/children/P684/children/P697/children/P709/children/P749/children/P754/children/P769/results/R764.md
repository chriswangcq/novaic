# App frontend and Monitor output contract discovery result

## Summary

App frontend/Monitor output contract discovery is complete across message media, Blob rendering, factory/raw JSON details, Monitor projection, and shell artifact UI surfaces. Active Chat, Monitor, and BlobRef preview paths are mostly aligned with the compact terminal-text plus BlobRef/artifact-reference contract. Real remediation candidates remain in non-active or separate UI surfaces: Factory Logs static raw/detail rendering, unused `SmartValue.tsx`, and legacy `AssistantMessage.tsx` events rendering.

## Done

- Closed `P773` / `R755`: App message media and Blob renderer discovery.
- Closed `P774` / `R759`: Factory log/raw JSON detail discovery, including factory static page, Monitor projection, and shared raw JSON primitive discovery.
- Closed `P775` / `R763`: Shell artifact output UI contract discovery across Chat, Monitor, and BlobRef preview surfaces.

## Verification

- `R755` records that Chat/media BlobRef rendering is already based on BlobRefs/cache/object URLs rather than inline base64 transport.
- `R759` records two remediation candidates: `novaic-llm-factory/static/factory-logs.html` raw JSON/detail scrubbing, and unused `novaic-app/src/components/Visual/SmartValue.tsx` raw arbitrary-value residue.
- `R763` records one remediation candidate: legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx`; it also confirms Monitor and BlobRef preview paths are clean.
- Targeted frontend tests passed in child tickets for ActivityTimeline, chat converters, BlobRef attachment paths, and chat message contract.
- No frontend/app UI files were modified in this discovery parent.

## Known Gaps

- Remediation candidate: safe client-side scrub/projection in `novaic-llm-factory/static/factory-logs.html`.
- Remediation candidate: remove unused `novaic-app/src/components/Visual/SmartValue.tsx`.
- Remediation candidate: remove or strictly narrow legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx`.
- This parent is discovery only; implementation belongs to follow-up optimization tickets.

## Artifacts

- Child results: `R755`, `R759`, `R763`
- Child checks: `C801`, `C805`, `C809`
