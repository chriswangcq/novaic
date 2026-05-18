# App Tauri backend and VmControl wiring discovery

## Problem

Discover whether `novaic-app/src-tauri` Rust/backend scripts and VmControl setup/startup paths still point at stale VMuse/Sandbox/Blob/LogicalFS entrypoints or imply outdated device/display/shell ownership. This belongs under P754 because app backend wiring decides what shipped resources actually run.

## Success Criteria

- Relevant Tauri Rust, setup, backend startup, and resource wiring files are discovered with bounded commands.
- Suspicious hits around `http_server`, FastMCP, VMuse, devicectl, display, screenshot, Blob, Sandbox, and LogicalFS are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Tauri/app wiring files are modified in this discovery child.
