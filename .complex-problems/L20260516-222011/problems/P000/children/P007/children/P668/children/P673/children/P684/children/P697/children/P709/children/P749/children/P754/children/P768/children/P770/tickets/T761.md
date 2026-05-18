# App Tauri Rust VmControl route wiring discovery ticket

## Problem Definition

Rust VmControl/setup route code in `novaic-app/src-tauri` may still start stale VMuse/FastMCP/direct-media entrypoints or misrepresent current device/display/shell, Blob, Sandbox, or LogicalFS ownership.

## Proposed Solution

Scan the Rust VmControl/setup route code and adjacent Tauri backend files for VMuse, HTTP server, FastMCP, devicectl, screenshot, display, Blob, Sandbox, LogicalFS, shell, and artifact references. Inspect high-signal slices to classify whether each startup path uses current HTTP/CLI wiring or stale direct MCP media wiring.

## Acceptance Criteria

- Relevant Rust route/setup files are discovered.
- Startup entrypoints and high-signal references are classified.
- Remediation candidates are listed precisely, or absence is explicitly recorded.
- No Rust/Tauri files are modified.

## Verification Plan

Use bounded `rg --files`, focused `rg -n -i`, and `sed` slices around high-signal Rust files under `novaic-app/src-tauri`.

## Risks

- `display` and `screenshot` terms may be legitimate VmControl/device concepts; classification must cite surrounding code, not keyword hits alone.

## Assumptions

- Runtime route wiring is represented in Rust source under `novaic-app/src-tauri`, especially VmControl route modules and setup routes.
