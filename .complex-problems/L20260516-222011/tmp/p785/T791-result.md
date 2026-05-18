# Result: App resource/generated and backend startup remediation

## Summary
App resource/generated VMuse copies, backend startup/package graph, app service config naming, stale VMuse MCP config, and VmControl HD screenshot comments were remediated through the four child problems under `P785`.

## Scope closed
- Synchronized the app VMuse committed resource copy with the source VMuse HTTP-only contract.
- Synchronized the generated Apple VMuse asset copy with the same cleaned contract.
- Cleaned the app backend startup graph so scripts/configs agree on current topology:
  - packaged and generated backend scripts now use `novaic-storage-a`
  - removed stale `novaic-blob-service` startup fallback from app backend scripts
  - added the missing packaged `resources/backends/novaic-storage-a` binary copy
  - renamed the app service config entry on port `19996` from `vmcontrol` to `cortex`
  - removed stale `runtime.vmuse_mcp_url` pointing at `http://127.0.0.1:8080/mcp`
  - clarified dev startup script wording so Cortex is treated as an external dependency for the dev subset
- Updated the VmControl HD screenshot route comments so they describe raw capture plus Blob/display artifact flow instead of direct LLM screenshot delivery.

## Child problem evidence
- `P800` (`R783`, `C830`): app VMuse resource copy sync completed.
- `P801` (`R784`, `C831`): generated Apple VMuse asset copy sync completed.
- `P802` (`R792`, `C840`): app backend startup graph cleanup completed.
- `P803` (`R793`, `C841`): VmControl HD screenshot contract comments completed.

## Verification evidence
- VMuse stale marker scans passed for resource and generated app copies.
- Resource/generated backend script and config copies compare equal after remediation.
- `bash -n` passed for app startup scripts.
- `python -m json.tool` passed for app service config JSON copies.
- Backend resource/generated directories compare cleanly after adding `resources/backends/novaic-storage-a`.
- Focused scans found no remaining `PORT_CORTEX`, `vmuse_mcp_url`, `8080/mcp`, or `novaic-blob-service` fallback references in the app backend startup/config paths.
- Focused HD route scans found no stale `sent to LLM`, `direct.*LLM`, `LLM.*screenshot`, `base64.*LLM`, or `screenshot.*LLM` wording in `hd_tools.rs`.

## Residual notes
- Broad VMControl Rust formatting checks still report pre-existing crate-wide formatting churn outside the HD comment edit; this was not treated as part of this app remediation ticket.
- Generated backend binaries are already tracked, while `novaic-app/src-tauri/resources/backends/novaic-storage-a` is newly added and must be staged when committing this remediation.
