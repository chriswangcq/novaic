# Cross-Service Semantic Residue Discovery And Classification Result

## Summary
Cross-service semantic residue discovery is complete. The scan covered active docs/scripts, service code, app resources/generated assets, frontend/monitor surfaces, VMuse/VmControl, Blob, LogicalFS, Sandboxd, shell, display, Queue/Runtime/Cortex, Gateway, Business, and Device. The findings are classified by surface and risk, and remediation candidates are explicit enough to implement without re-auditing the whole repository.

## Evidence
- `R736` covers active docs/scripts and identifies active documentation wording that needs sharpening around Cortex, LogicalFS, and Sandboxd ownership.
- `R749` covers service code and identifies exact residue candidates across Runtime/Cortex, Business, Device, LogicalFS, Sandbox, VMuse, and app resource copies.
- `R765` covers app resource/generated assets plus frontend/log UI surfaces and identifies stale app scripts, generated-copy sync work, Factory Logs UI residue, unused `SmartValue`, and legacy `AssistantMessage` events rendering.

## Criteria Map
- `Targeted scans cover service-boundary terms for Cortex, Gateway, Business, Device/devicectl, Queue, Runtime, Blob, LogicalFS, Sandboxd, shell, display, and VMuse/VmControl`: satisfied by `R736`, `R749`, and `R765`.
- `Findings are grouped by file/surface and classified as active, stale, generated, historical, lower-level protocol, or test/fixture`: satisfied; the child results distinguish active docs, active code, generated/copied app assets, historical roadmap/ticket docs, lower-level protocol references, and tests/fixtures.
- `Exact remediation candidates are listed for the next child problem`: satisfied in Known Gaps.
- `Broad risky areas are called out instead of silently accepted`: satisfied; generated assets, compatibility display/media paths, app startup scripts, and inactive frontend renderers are all explicitly called out.

## Execution Map
- Completed `P752/R736`: active docs and scripts semantic residue discovery.
- Completed `P753/R749`: service code semantic residue discovery.
- Completed `P754/R765`: app resource and generated asset semantic residue discovery.

## Stress Test
- I did not treat historical roadmap/ticket docs as active product claims unless the child result identified them as active instructions.
- I did not patch generated assets during discovery, because that would blur source-of-truth boundaries.
- I did not treat passing focused tests as proof of no residue; unused renderers and stale packaged scripts remain listed because they can mislead future agents and maintainers.

## Residual Risk
- This parent is a discovery/classification closure, not remediation. The next problem must implement the backlog and verify with focused tests plus diff review.
- Some generated app assets may need synchronization policy confirmation during implementation: either regenerate them or patch them in a clearly synchronized way with source/resource files.

## Known Gaps
- Docs/scripts:
  - Clarify `docs/architecture/logicalfs-realtime-file-authority.md` so LogicalFS is file-operation/view substrate, while Cortex remains semantic owner.
  - Update `docs/architecture/cortex.md` and `docs/cortex-architecture.md` wording around `sandbox.py` so Cortex orchestrates shell/workspace semantics, delegates execution to Sandboxd, and uses LogicalFS as substrate.
  - Sharpen `docs/architecture/data-ownership.md`: Cortex owns scope/context/workspace semantics, LogicalFS owns live RO/RW file operations/view contract, Blob owns bytes.
- Runtime/Cortex:
  - Reword `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` docstring that overstates Cortex as the single gateway to agent storage.
  - Narrow/delete direct MCP inline image data and data URL compatibility in `novaic-cortex/novaic_cortex/step_result_projection.py` if final display/media contract is BlobRef-only.
- Gateway/Business/Device:
  - Reword `novaic-business/business/internal/message.py` cancellation wording so it does not imply direct Queue bypass.
  - Clean stale CASCADE cleanup comment in `novaic-device/device/config_agents_db.py`.
  - Inspect/narrow historical Entangled wording in `novaic-device/device/entity_store.py`.
- LogicalFS/Sandbox:
  - Update LogicalFS public docs/metadata to emphasize live `/ro` and `/rw` authority rather than snapshot/view/patch phrasing.
  - Delete or relocate unused Sandbox filesystem helper surface and its exports/tests if confirmed inactive.
- VMuse/App resources:
  - Remove stale FastMCP direct-media entry path from source VMuse and synchronize copied app resource/generated asset trees.
  - Fix app backend startup/package graph and `PORT_CORTEX=19996` versus `vmcontrol` port naming conflict.
  - Update stale HD tools screenshot-to-LLM comment.
- App/frontend/log UI:
  - Add safe scrub/projection to `novaic-llm-factory/static/factory-logs.html`.
  - Delete unused `novaic-app/src/components/Visual/SmartValue.tsx` if still unused.
  - Remove or narrow legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx`.

## Result IDs
- Child results: `R736`, `R749`, `R765`.
- Child checks: `C781`, `C795`, `C811`.
