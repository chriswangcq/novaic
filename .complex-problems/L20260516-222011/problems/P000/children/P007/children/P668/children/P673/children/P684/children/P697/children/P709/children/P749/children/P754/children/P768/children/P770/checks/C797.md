# App Tauri Rust VmControl route wiring discovery check

## Summary

Success. The Rust route discovery met its scoped criteria: relevant route/setup files were found, high-signal VMUSE/device/media/blob hits were classified, and exact remediation candidates were recorded. The one-go path is acceptable because it was read-only, bounded, and produced a concrete scan artifact plus file-level classifications.

## Evidence

- `R751` cites the scan artifact `.complex-problems/L20260516-222011/tmp/p770-rust-route-scan.txt`.
- `R751` confirms VMUSE startup/sync uses `novaic_mcp_vmuse.http_server` via `vmuse.rs`, not FastMCP `main.py`.
- `R751` classifies `hd_tools.rs`, `mobile.rs`, `screen.rs`, and `qmp.rs` base64 as lower-level route/API transport, not direct LLM context assembly.
- `R751` records the app Blob fetch contract in `src/commands/file.rs`.
- `R751` lists one exact remediation candidate: stale "sent to LLM" wording in `hd_tools.rs`.

## Criteria Map

- Relevant Rust route/setup files discovered: satisfied by the file list and inspected slices in the scan artifact.
- Suspicious references classified: satisfied by `R751` classifying HTTP server startup, route-level base64, app Blob fetch, and stale wording.
- Exact remediation candidates listed or absence recorded: satisfied by the `hd_tools.rs` comment candidate and absence of FastMCP route startup wiring.
- No Rust/Tauri files modified: satisfied by `R751`; this child only wrote ledger artifacts.

## Execution Map

- The ticket executed bounded search over `novaic-app/src-tauri`.
- It inspected targeted slices around VMUSE install/sync/proxy, host desktop screenshot, mobile screenshot, VM QMP screenshot, route registration, and Blob file fetch.
- It recorded a result without performing remediation, matching the discovery-only boundary.

## Stress Test

- Plausible failure mode: Rust setup could still launch `novaic_mcp_vmuse.main` or FastMCP. The inspected `vmuse_service_unit` uses `python3 -m novaic_mcp_vmuse.http_server`, and source location checks for `http_server.py`.
- Plausible failure mode: base64 route hits could indicate the old LLM-context bug. The inspected route code returns API JSON to devicectl/app callers; the direct LLM projection layer is outside this Rust slice.
- Plausible failure mode: app file display could bypass Blob. `src/commands/file.rs` explicitly requires `blob://` and maps it to Blob edge download.

## Residual Risk

- This child did not inspect frontend monitor display behavior or app scripts; those are separate children under P768/P769.
- The stale `hd_tools.rs` wording remains to be remediated later. It is not blocking discovery success.

## Result IDs

- R751
