# App backend script and launch wiring discovery result

## Summary

App backend launch scripts were scanned. No script directly starts stale VMUSE FastMCP `main.py` as the active runtime service; VMUSE resource sync/build scripts copy the source tree into app resources. However, script-level backend orchestration is stale relative to the newer service split: local and packaged app startup scripts still describe/start only a subset, omit Cortex/Sandboxd/LogicalFS, and pass workers a `CORTEX_URL` on port `19996` even though the app resource service config names port `19996` as `vmcontrol`. These are precise remediation candidates.

## Done

- Scanned app scripts, package scripts, Tauri config/resources, and generated packaged backend scripts.
- Inspected:
  - `novaic-app/package.json`
  - `novaic-app/scripts/start-backends.sh`
  - `novaic-app/scripts/sync-vmuse-resource.sh`
  - `novaic-app/scripts/build-dmg.sh`
  - `novaic-app/src-tauri/resources/config/services.json`
  - `novaic-app/src-tauri/resources/backends/start-backends.sh`
  - `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`
- Classified VMUSE sync/build hits, backend service startup hits, Blob/Gateway/Queue/Cortex/Sandbox references, and copied resource script references.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p771-backend-script-scan.txt`.
- `novaic-app/package.json` runs `bash scripts/sync-vmuse-resource.sh` before `tauri build`; that script copies the VMUSE source tree into resource/generated app bundles.
- `novaic-app/scripts/sync-vmuse-resource.sh` checks for `src/novaic_mcp_vmuse/main.py` as a source-tree presence check and then rsyncs the whole VMUSE repo; this is copy synchronization, not direct runtime startup.
- `novaic-app/scripts/start-backends.sh` starts Gateway, Queue Service, Blob Service, and runtime workers, but explicitly says Cortex/Sandboxd are not started.
- `novaic-app/scripts/start-backends.sh` defines `PORT_CORTEX=19996` and passes `--cortex-url http://127.0.0.1:19996` to task/saga/scheduler workers.
- `novaic-app/src-tauri/resources/config/services.json` names port `19996` as `vmcontrol`, not `cortex`.
- `novaic-app/src-tauri/resources/backends/start-backends.sh` and the generated Apple asset copy start only Blob Service, Gateway, and an Agent Runtime process, while explicitly saying Cortex/Sandboxd are not started.

## Known Gaps

- Remediation candidate: update or replace `novaic-app/scripts/start-backends.sh` so its service graph matches the current backend architecture, including explicit Cortex/Sandboxd/LogicalFS handling or a clear external dependency contract.
- Remediation candidate: remove the misleading `PORT_CORTEX=19996` / `--cortex-url` wiring conflict with `vmcontrol` port `19996`, or make the intended local Cortex endpoint explicit and non-conflicting.
- Remediation candidate: update packaged backend scripts in:
  - `novaic-app/src-tauri/resources/backends/start-backends.sh`
  - `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`
  so they no longer advertise an incomplete/stale backend subset as the packaged app runtime path.
- No script/package files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p771-backend-script-scan.txt`
