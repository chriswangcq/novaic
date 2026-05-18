# App Tauri backend and VmControl wiring discovery aggregate result

## Summary

P768 split discovery is complete. Rust VmControl routes mostly point at the current VMUSE HTTP server path, but app backend scripts and packaged resources still contain stale/incomplete backend service graph assumptions. The key remediation direction is not Rust VMUSE route startup; it is app backend startup/package graph cleanup: align Cortex/Sandboxd/LogicalFS/Blob/Queue/Gateway service ownership, remove port conflicts, and synchronize generated resources.

## Done

- Completed P770 (`R751`): Rust VmControl route wiring discovery.
- Completed P771 (`R752`): app backend script and launch wiring discovery.
- Completed P772 (`R753`): app resource packaging and generated asset wiring discovery.
- Aggregated child remediation candidates into parent P768.

## Verification

- `R751` shows VMUSE sync/service unit uses `python3 -m novaic_mcp_vmuse.http_server`, not stale FastMCP `main.py`.
- `R751` classifies route-level screenshot/base64 as lower-level API transport and identifies one stale wording candidate in `hd_tools.rs`.
- `R752` shows local `start-backends.sh` starts Gateway, Queue Service, Blob Service, and workers, but explicitly does not start Cortex/Sandboxd while still passing `--cortex-url` to workers.
- `R752` shows `PORT_CORTEX=19996` conflicts with app resource `services.json`, which names `19996` as `vmcontrol`.
- `R753` shows source resources and generated Apple assets are synchronized for key text resources, so stale resource scripts/config/VMUSE copies propagate together.
- `R753` shows packaged backend assets are inconsistent: script expects `novaic-blob-service`, source resources do not ship that binary, and generated Apple assets include extra `novaic-storage-a`.

## Known Gaps

- Remediation candidate: update `novaic-app/scripts/start-backends.sh` to match the current backend architecture or explicitly become a narrow dev-only helper that does not start workers requiring missing services.
- Remediation candidate: resolve the `PORT_CORTEX=19996` / `vmcontrol` port naming conflict in app backend scripts and config.
- Remediation candidate: update `novaic-app/src-tauri/resources/backends/start-backends.sh` and `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh` together.
- Remediation candidate: align backend binaries shipped in `resources/backends` and generated Apple assets with the startup script.
- Remediation candidate: propagate VMUSE FastMCP/direct-media cleanup into bundled resources/generated assets after source cleanup.
- Remediation candidate: update stale `hd_tools.rs` comment that says screenshots are sent to LLM.
- No app backend/resource files were modified in this discovery parent.

## Artifacts

- P770 result `R751`
- P771 result `R752`
- P772 result `R753`
- `.complex-problems/L20260516-222011/tmp/p770-rust-route-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p771-backend-script-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p772-resource-packaging-scan.txt`
