# App Tauri backend and VmControl wiring discovery ticket

## Problem Definition

`novaic-app/src-tauri` backend and VmControl startup paths may still point at stale VMuse, Sandbox, Blob, LogicalFS, device/display, screenshot, or shell ownership paths even after the CLI/display/blob contract cleanup.

## Proposed Solution

Run a bounded discovery over Tauri Rust backend code, setup routes, scripts, and resource wiring files. Classify high-signal hits as current HTTP/CLI wiring, stale FastMCP/direct media wiring, intentional lower-level transport, or unrelated vocabulary. Record exact remediation candidates or explicitly record none.

## Acceptance Criteria

- Relevant Tauri Rust/backend script/resource wiring files are discovered.
- High-signal `http_server`, FastMCP, VMuse, devicectl, display, screenshot, Blob, Sandbox, LogicalFS, shell, and artifact hits are classified.
- Startup/runtime entrypoints are checked for whether they execute HTTP server/CLI paths or old MCP direct media paths.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Tauri/app wiring files are modified.

## Verification Plan

Use `rg --files` and focused `rg -n -i` under `novaic-app/src-tauri` and `novaic-app/scripts`; inspect the highest-signal Rust setup/startup files and scripts with bounded `sed` slices; record scan artifacts in the ledger tmp directory.

## Risks

- Some generated resource paths may intentionally mirror source assets and should not be edited directly during discovery.
- Search hits for `display` and `screenshot` may be current device/UI concepts rather than stale direct LLM media contracts, so classification must be evidence-based.

## Assumptions

- App backend startup and VmControl wiring are concentrated under `novaic-app/src-tauri` and `novaic-app/scripts`.
- This ticket is discovery-only; remediation happens later through follow-up or parent cleanup.
