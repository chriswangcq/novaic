# App Tauri Rust VmControl route wiring discovery

## Problem

Discover whether `novaic-app/src-tauri` Rust VmControl/setup routes still start stale VMuse/FastMCP/direct-media entrypoints or imply outdated ownership for device/display/shell, Blob, Sandbox, or LogicalFS. This belongs under P768 because Rust routes decide which VM service and command paths the packaged app invokes.

## Success Criteria

- Relevant Rust route/setup files under `novaic-app/src-tauri` are discovered with bounded commands.
- Hits for `http_server`, FastMCP, VMuse, devicectl, display, screenshot, Blob, Sandbox, LogicalFS, shell, and artifact are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Rust/Tauri files are modified in this discovery child.
