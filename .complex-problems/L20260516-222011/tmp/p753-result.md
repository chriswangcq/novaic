# Service code semantic residue discovery result

## Summary

The split service-code semantic residue discovery completed across Runtime/Queue/Cortex, Gateway/Business/Device, and Blob/LogicalFS/Sandbox/VMuse/app-copy service families. The discovery produced a concrete remediation backlog and did not modify product code.

## Done

- Closed P755 / R737: Runtime Queue Cortex service-code residue discovery.
- Closed P756 / R738 plus follow-up P758 / R742: Gateway Business Device source and test residue discovery.
- Closed P757 / R748: Blob LogicalFS Sandbox VMuse service-code residue discovery.

## Verification

- P755 result R737 classifies Runtime/Queue/Cortex findings and lists exact Runtime/Cortex candidates.
- P756 final check C788 covers active source plus Gateway/Business/Device test follow-ups.
- P757 check C794 covers Blob, LogicalFS, Sandbox, VMuse, and copied app resources.
- Focused test evidence recorded by children includes LogicalFS `10 passed`, Sandbox `16 passed`, VMuse `1 passed`, plus prior Gateway/Business/Device test discovery results.

## Known Gaps

- Remediation candidates to pass into the later remediation branch:
  - Runtime/Cortex: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` docstring overstates Cortex as the single gateway to agent storage.
  - Cortex: `novaic-cortex/novaic_cortex/step_result_projection.py` still accepts direct MCP inline image data and data URLs for display perception; if BlobRef-only display/media is final, narrow or delete that compatibility path with tests.
  - Business: `novaic-business/business/internal/message.py` says `Cancellation executed directly via Queue Service`; reword to avoid implying bypass.
  - Device: `novaic-device/device/config_agents_db.py` has stale historical CASCADE cleanup table commentary.
  - Device: inspect and possibly narrow historical Entangled wording in `novaic-device/device/entity_store.py`.
  - LogicalFS: public docs/metadata still over-emphasize snapshot/view/patch and should mention live `/ro` and `/rw` authority.
  - Sandbox: unused filesystem helper surface exists only through exports/tests and should be deleted or relocated.
  - VMuse: stale FastMCP direct media entry path remains reachable through source `main.py`/`cli.py`/`pyproject.toml`.
  - App resources: copied VMuse resource/generated trees mirror the stale FastMCP path and must be synchronized during remediation.
- No product code was modified in this discovery ticket.

## Artifacts

- R737
- R738
- R742
- R748
