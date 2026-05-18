# App Backend Startup Graph Audit Result

## Summary

Mapped the app backend startup graph without editing code. The startup surface is split across a source/dev script, two packaged script copies, two service config copies, and committed backend binaries. The graph has concrete inconsistencies that should be remediated in P805.

## Done

- Listed current startup scripts:
  - `novaic-app/scripts/start-backends.sh`
  - `novaic-app/src-tauri/resources/backends/start-backends.sh`
  - `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`
- Listed current service config copies:
  - `novaic-app/src-tauri/resources/config/services.json`
  - `novaic-app/src-tauri/gen/apple/assets/config/services.json`
- Compared committed backend binaries:
  - Resource copy has `novaic-agent-runtime`, `novaic-gateway`, `novaic-runtime-orchestrator`, `start-backends.sh`.
  - Generated asset copy has those plus `novaic-storage-a`.
- Mapped service ports from evidence:
  - App config: gateway `19999`, queue_service `19997`, vmcontrol `19996`, blob_service `19995`.
  - Source/dev script: gateway `19999`, business `19998`, queue_service `19997`, `PORT_CORTEX=19996`, blob_service `19995`.
  - Packaged scripts: gateway `19999`, blob_service `19995`.
- Confirmed the packaged scripts expect a `novaic-blob-service` binary, but the generated packaged assets contain `novaic-storage-a` instead and the source resource backend directory contains neither blob binary.

## Verification

- Ran `find` over app script/resource/generated asset locations to enumerate `start-backends.sh` and `services.json`.
- Ran targeted `rg` over app scripts/config/resources for `PORT_CORTEX`, `vmcontrol`, `vmuse_mcp_url`, `novaic-storage-a`, `novaic-blob-service`, `BLOB_SERVICE`, `cortex-url`, and `blob-service`.
- Read `novaic-app/scripts/start-backends.sh`, both packaged `start-backends.sh` copies, and `resources/config/services.json`.
- Ran `ls -l` over resource and generated backend binary directories.

## Known Gaps

- P805 should remediate the backend graph rather than leaving these inconsistencies as documentation only.
- The source/dev script still names port `19996` as Cortex while app config names the same port `vmcontrol`; worker `--cortex-url` wiring needs source-level clarification before changing behavior.
- The packaged scripts and committed binaries disagree on blob service binary name/source: scripts look for `novaic-blob-service`, generated assets have `novaic-storage-a`, and resources lack a blob binary.
- `runtime.vmuse_mcp_url` still points to `http://127.0.0.1:8080/mcp`; this needs usage inspection because VMuse was just cleaned to HTTP JSON routes.

## Artifacts

- Audit-only ticket; no code files edited.
