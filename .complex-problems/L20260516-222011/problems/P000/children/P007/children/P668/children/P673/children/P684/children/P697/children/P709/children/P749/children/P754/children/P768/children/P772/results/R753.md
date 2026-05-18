# App resource packaging and generated asset wiring discovery result

## Summary

App resource packaging and generated assets were scanned. The resource/gen copies are synchronized for service config, packaged backend startup script, and VMUSE source files, which means stale resource behavior is shared rather than isolated. Several packaging-level remediation candidates were found: bundled backend assets do not line up with the startup script names, generated Apple assets contain an extra `novaic-storage-a` binary not present in source resources, service config still names port `19996` as `vmcontrol`, and VMUSE FastMCP/direct-media source residue is bundled on all platforms through Tauri resources.

## Done

- Scanned Tauri resource manifests, resource directories, generated Apple assets, app scripts, and service config files.
- Compared source resource and generated Apple asset checksums for:
  - `config/services.json`
  - `backends/start-backends.sh`
  - `novaic-mcp-vmuse/run_server.sh`
  - `novaic-mcp-vmuse/pyproject.toml`
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/cli.py`
  - `novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py`
- Inspected Tauri bundle resource mappings for desktop, iOS, and Android.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p772-resource-packaging-scan.txt`.
- Desktop, iOS, and Android Tauri configs bundle `resources/config`, `resources/backends`, and `resources/novaic-mcp-vmuse`.
- Resource/gen checksums match for `config/services.json`, `backends/start-backends.sh`, and representative VMUSE files. This proves generated Apple assets currently mirror source resources for those files.
- `novaic-app/src-tauri/resources/backends` contains `novaic-agent-runtime`, `novaic-gateway`, `novaic-runtime-orchestrator`, and `start-backends.sh`.
- `novaic-app/src-tauri/gen/apple/assets/backends` additionally contains `novaic-storage-a`, which is absent from source resources.
- `backends/start-backends.sh` expects a `novaic-blob-service` binary, but source resources do not contain `novaic-blob-service`.
- `resources/config/services.json` and generated copy are byte-identical and name service port `19996` as `vmcontrol`.
- Bundled VMUSE `main.py`/`cli.py` still contain the stale FastMCP/direct-media source residue identified in earlier VMUSE copy discovery.

## Known Gaps

- Remediation candidate: align `novaic-app/src-tauri/resources/backends/start-backends.sh` with the actual backend binaries shipped in `resources/backends`, or replace the resource backend bundle with the current service graph.
- Remediation candidate: remove or regenerate stale generated Apple asset `novaic-app/src-tauri/gen/apple/assets/backends/novaic-storage-a` if it is not part of the current authoritative resource set.
- Remediation candidate: update the generated/source packaged backend scripts together because their checksums match and they share stale backend subset wording.
- Remediation candidate: update packaged service config once the app backend graph is corrected, especially the `19996` `vmcontrol` vs `CORTEX_URL` conflict discovered in P771.
- Remediation candidate: propagate VMUSE FastMCP/direct-media cleanup into bundled resource and generated asset copies.
- No resource/package wiring files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p772-resource-packaging-scan.txt`
