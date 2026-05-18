# App Tauri Rust VmControl route wiring discovery result

## Summary

Rust/Tauri VmControl route wiring was scanned. The VMUSE service installation and sync paths correctly target `novaic_mcp_vmuse.http_server`, not the stale FastMCP `main.py` path. Screenshot/base64 remains present in lower-level VmControl routes as API transport (`hd_tools`, VM QMP screenshot, Android screenshot), but it is not the old direct MCP ImageContent path. One precise cleanup candidate was found: `hd_tools.rs` still describes screenshot downscaling as "sent to LLM", which is stale wording after the Blob/display contract.

## Done

- Scanned Rust/Tauri route and configuration files under `novaic-app/src-tauri`.
- Inspected high-signal route slices in:
  - `novaic-app/src-tauri/vmcontrol/src/api/routes/setup.rs`
  - `novaic-app/src-tauri/vmcontrol/src/api/routes/vmuse.rs`
  - `novaic-app/src-tauri/vmcontrol/src/api/routes/hd_tools.rs`
  - `novaic-app/src-tauri/vmcontrol/src/api/routes/mobile.rs`
  - `novaic-app/src-tauri/vmcontrol/src/api/routes/screen.rs`
  - `novaic-app/src-tauri/vmcontrol/src/qemu/qmp.rs`
  - `novaic-app/src-tauri/src/commands/file.rs`
- Classified startup and media hits as current HTTP/server wiring, lower-level API transport, frontend blob fetching, or stale wording.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p770-rust-route-scan.txt`.
- `setup.rs` cloud-init enables `novaic-vmuse`; it does not reference FastMCP or `main.py`.
- `vmuse.rs` locates VMUSE source by checking for `http_server.py` and writes a systemd unit with `ExecStart=/opt/novaic/venv/bin/python3 -m novaic_mcp_vmuse.http_server`.
- `vmuse.rs` generic proxy forwards to the VMUSE HTTP server at `http://localhost:8080/api/{tool}/{operation}`.
- `hd_tools.rs`, `mobile.rs`, `screen.rs`, and `qmp.rs` still use base64 for route/API payload transport, but the surrounding code is route-level device or VM transport, not direct LLM message assembly.
- `src/commands/file.rs` accepts `blob://` references and fetches bytes from the direct Blob edge, matching the app-side display/download contract.

## Known Gaps

- Remediation candidate: update the stale comment in `novaic-app/src-tauri/vmcontrol/src/api/routes/hd_tools.rs` from "screenshots sent to LLM" to route/API transport wording such as "screenshots returned to devicectl/runtime callers".
- No Rust/Tauri route files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p770-rust-route-scan.txt`
