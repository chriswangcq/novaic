# App Resource And Generated Asset Semantic Residue Discovery Result

## Summary
App resource/generated discovery is complete. It found no need to manually patch generated assets during discovery, but it found real remediation candidates spanning VMuse copied resources, app backend startup/package graph, stale HD tools comments, and App frontend/log UI residue. Source-of-truth versus generated/copy boundaries are explicit: VMuse copies should be synchronized from source after source cleanup, and generated Apple assets should be regenerated or synchronized with resource changes rather than manually diverged.

## Evidence
- Child `P767/R750` audited VMuse copied resource trees and found they currently mirror source, including stale FastMCP/direct-media paths in the copied `main.py`, `cli.py`, `__init__.py`, and `pyproject.toml` files.
- Child `P768/R754` audited App Tauri backend and VmControl wiring. Rust VmControl launch paths mostly use the current VMUSE HTTP service, but app backend scripts/resources remain stale or incomplete, and script port naming conflicts with `services.json`.
- Child `P769/R764` audited frontend and Monitor output contracts. Active Chat, Monitor ActivityTimeline, and BlobRef preview paths are mostly clean, but Factory Logs static detail UI, unused `SmartValue`, and legacy `AssistantMessage` events rendering remain remediation candidates.

## Criteria Map
- `scans cover novaic-app resource and generated asset locations relevant to VMuse, Device, display, and shell tooling`: satisfied by `P767`, `P768`, and `P769`.
- `findings distinguish generated copies from source-of-truth code/docs`: satisfied; VMuse app trees and Apple asset trees are recorded as copies/generated assets, while source VMuse cleanup remains a separate source-of-truth concern.
- `required sync/remediation candidates are listed for remediation child`: satisfied in the Known Gaps section below.
- `no generated assets manually patched in discovery child`: satisfied; this discovery parent only inspected and recorded findings.

## Execution Map
- Completed `P767/R750`: App VMuse copied resource sync discovery.
- Completed `P768/R754`: App Tauri backend and VmControl wiring discovery.
- Completed `P769/R764`: App frontend and Monitor output contract discovery.

## Stress Test
- I treated copied/generated resources as dangerous to patch directly during discovery and only recorded synchronization candidates.
- I separated active user-facing paths from inactive but dangerous residue so remediation can delete or narrow the latter without mistaking it for a live path.
- I checked that current passing frontend contract tests do not by themselves prove the stale App scripts/resources are clean; those remain explicit implementation work.

## Residual Risk
- The discovery does not itself fix the residue. Remediation tickets should update source and synchronized copies together, then run focused app/runtime tests.
- App generated Apple assets may be produced by packaging workflows. If the repository expects committed generated assets, remediation must keep them in sync; otherwise it should document or enforce regeneration.

## Known Gaps
- Sync VMuse source cleanup into app resource/generated copy trees.
- Fix App backend startup/package graph and the `PORT_CORTEX=19996` versus `vmcontrol` port naming conflict.
- Update stale HD tools screenshot-to-LLM comment in VmControl Rust code.
- Add safe scrub/projection to `novaic-llm-factory/static/factory-logs.html`.
- Delete unused `novaic-app/src/components/Visual/SmartValue.tsx` if confirmed unused at implementation time.
- Remove or narrow legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx`.

## Result IDs
- Child results: `R750`, `R754`, `R764`.
- Child checks: `C796`, `C800`, `C810`.
