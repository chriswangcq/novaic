# App resource packaging and generated asset wiring discovery ticket

## Problem Definition

App resource packaging and generated asset wiring may copy or ship stale VMUSE/Sandbox/Blob/LogicalFS resources, backend scripts, or service configs after source cleanup.

## Proposed Solution

Scan app Tauri resource manifests, generated Apple assets, bundled backend scripts, service config files, and VMUSE resource packaging references. Compare generated/resource copies where relevant and classify whether stale behavior is copied source residue, packaging drift, or current runtime configuration.

## Acceptance Criteria

- Relevant resource packaging and generated asset wiring files are discovered.
- Copied resource/script/config hits are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No resource/package wiring files are modified.

## Verification Plan

Use bounded `rg --files`, focused `rg -n -i`, and checksum/diff comparisons under `novaic-app/src-tauri/resources`, `novaic-app/src-tauri/gen/apple/assets`, `tauri.conf.json`, and build scripts.

## Risks

- Generated assets may be regenerated from source resources, so remediation should target the authoritative source or the sync/generation script when possible.

## Assumptions

- Resource packaging state is represented by `novaic-app/src-tauri/resources`, `novaic-app/src-tauri/gen/apple/assets`, Tauri config files, and app build/sync scripts.
