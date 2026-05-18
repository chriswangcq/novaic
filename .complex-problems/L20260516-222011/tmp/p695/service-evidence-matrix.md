# Service Evidence Matrix

This is discovery evidence only. Role classification and cleanup are handled by sibling problems.


## blob

- candidate_path_matches: 51
- launch_reference_matches: 588

### Candidate paths (first 30)

```text
docs/blob-service-architecture.md
docs/reference/blob-audio.md
docs/reference/blob-service.md
docs/roadmap/blob-large-file-multipart-audio.md
docs/roadmap/tickets/PR-199-blob-service-contract-domain-model.md
docs/roadmap/tickets/PR-200-blob-service-foundation.md
docs/roadmap/tickets/PR-201-unified-resource-ref-blob-uri.md
docs/roadmap/tickets/PR-202-cortex-payload-blob-externalization.md
docs/roadmap/tickets/PR-203-app-gateway-blob-attachment-access.md
docs/roadmap/tickets/PR-204-blob-historical-data-migration-or-purge.md
docs/roadmap/tickets/PR-206-blob-e2e-smoke-and-deployment.md
docs/roadmap/tickets/PR-207-cortex-blob-store-cutover.md
docs/roadmap/tickets/PR-211-blob-large-file-multipart-audio-review.md
docs/roadmap/tickets/PR-212-blob-multipart-contract-backend.md
docs/roadmap/tickets/PR-215-blob-payload-limits-observability.md
docs/roadmap/tickets/PR-216-remove-base64-blob-upload.md
docs/roadmap/tickets/PR-217-direct-blob-download-edge.md
novaic-app/src/application/blobAttachmentPath.test.ts
novaic-blob-service/README.md
novaic-blob-service/blob_service/__init__.py
novaic-blob-service/blob_service/backends.py
novaic-blob-service/blob_service/blob_storage.py
novaic-blob-service/blob_service/contracts.py
novaic-blob-service/blob_service/limits.py
novaic-blob-service/blob_service/main.py
novaic-blob-service/blob_service/multipart_storage.py
novaic-blob-service/blob_service/object_storage.py
novaic-blob-service/blob_service/routes.py
novaic-blob-service/blob_service/storage.py
novaic-blob-service/main_blob_service.py
```

### Launch references (first 30)

```text
./README.md:16:├── novaic-blob-service/         # Blob Service
./scripts/start.sh:12:#   - Gateway        :19999  Auth, App WS signaling, log broadcast, Blob edge
./scripts/start.sh:140:    for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:151:for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:194:    --queue-service-url "$QS_URL" --blob-service-url "$BLOB_URL" \
./scripts/start.sh:225:$(py novaic-blob-service) "$BASE/novaic-blob-service/main_blob_service.py" \
./scripts/start.sh:227:    >> "$LOG_DIR/blob-service.log" 2>&1 &
./scripts/start.sh:228:wait_port "$PORT_BLOB_SERVICE" "Blob Service"
./scripts/start.sh:246:CORTEX_BLOB_SERVICE_URL="$BLOB_URL" \
./scripts/start.sh:252:	    --blob-service-url "$BLOB_URL" \
./novaic-app/src/services/fileUpload.ts:220: * Upload a single File to the Blob Service via Gateway.
./novaic-app/src/services/fileUpload.ts:222: * All chat attachments use the direct multipart Blob upload edge. Gateway
./scripts/build-all.sh:48:    "novaic-blob-service"
./scripts/build-all.sh:107:echo "  $BUILD_DIR/novaic-blob-service --port 19995"
./scripts/run_all_tests.sh:71:run_pytest "logicalfs" "novaic-logicalfs" ".:../novaic-common:../novaic-blob-service"
./scripts/run_all_tests.sh:77:run_pytest "blob-service" "novaic-blob-service" ".:../novaic-common"
./HANDOVER.md:26:  Blob-backed payload references. Cortex does not own product memory.
./novaic-cortex/novaic_cortex/workspace.py:71:from novaic_cortex.blob_payload import (
./novaic-cortex/novaic_cortex/workspace.py:581:                raise RuntimeError("large Cortex payload requires CORTEX_BLOB_SERVICE_URL")
./novaic-cortex/novaic_cortex/workspace.py:657:                    message="external Cortex payload requires CORTEX_BLOB_SERVICE_URL",
./novaic-sandbox-service/tests/test_sandbox_boundary.py:14:def test_sandbox_service_does_not_import_cortex_blob_or_logicalfs() -> None:
./novaic-sandbox-service/tests/test_sandbox_boundary.py:40:        "BlobCortexStore",
./scripts/ci/lint_blob_workspace_boundary.py:2:"""Lint the Blob/LogicalFS authority boundary from the repository root.
./scripts/ci/lint_blob_workspace_boundary.py:4:Blob is the byte store. LogicalFS is the live workspace authority. This guard
./scripts/ci/lint_blob_workspace_boundary.py:18:POLICY_PATH = REPO_ROOT / "novaic-cortex" / "cortex_tests" / "blob_boundary_policy.py"
./scripts/ci/lint_blob_workspace_boundary.py:20:    REPO_ROOT / "novaic-cortex" / "novaic_cortex",
./scripts/ci/lint_blob_workspace_boundary.py:21:    REPO_ROOT / "novaic-logicalfs" / "logicalfs",
./scripts/ci/lint_blob_workspace_boundary.py:22:    REPO_ROOT / "novaic-sandbox-service" / "sandbox_service",
./scripts/ci/lint_blob_workspace_boundary.py:53:    cortex_root = REPO_ROOT / "novaic-cortex"
./scripts/ci/lint_blob_workspace_boundary.py:54:    if path.is_relative_to(cortex_root):
```

## logicalfs

- candidate_path_matches: 11
- launch_reference_matches: 324

### Candidate paths (first 30)

```text
docs/architecture/logicalfs-realtime-file-authority.md
novaic-logicalfs/README.md
novaic-logicalfs/logicalfs/__init__.py
novaic-logicalfs/logicalfs/authority.py
novaic-logicalfs/logicalfs/blob_store.py
novaic-logicalfs/logicalfs/contracts.py
novaic-logicalfs/logicalfs/local.py
novaic-logicalfs/pyproject.toml
novaic-logicalfs/tests/test_authority.py
novaic-logicalfs/tests/test_blob_store.py
novaic-logicalfs/tests/test_logicalfs.py
```

### Launch references (first 30)

```text
./scripts/start.sh:247:PYTHONPATH="$BASE/novaic-cortex:$BASE/novaic-logicalfs:$BASE/novaic-sandbox-sdk:$BASE/novaic-common:${PYTHONPATH:-}" \
./scripts/run_all_tests.sh:71:run_pytest "logicalfs" "novaic-logicalfs" ".:../novaic-common:../novaic-blob-service"
./scripts/run_all_tests.sh:76:run_pytest "cortex" "novaic-cortex" ".:../novaic-logicalfs:../novaic-sandbox-sdk:../novaic-common"
./novaic-cortex/novaic_cortex/workspace.py:218:        LogicalFS: callers work in logical workspace paths, while Workspace
./novaic-sandbox-service/tests/test_sandbox_boundary.py:14:def test_sandbox_service_does_not_import_cortex_blob_or_logicalfs() -> None:
./novaic-sandbox-service/tests/test_sandbox_boundary.py:18:        "logicalfs",
./scripts/ci/lint_blob_workspace_boundary.py:2:"""Lint the Blob/LogicalFS authority boundary from the repository root.
./scripts/ci/lint_blob_workspace_boundary.py:4:Blob is the byte store. LogicalFS is the live workspace authority. This guard
./scripts/ci/lint_blob_workspace_boundary.py:21:    REPO_ROOT / "novaic-logicalfs" / "logicalfs",
./novaic-cortex/novaic_cortex/sandbox.py:5:* ``MountNamespaceLogicalFS`` owns Cortex filesystem semantics and the stable
./novaic-cortex/novaic_cortex/sandbox.py:25:    LogicalFSCapabilities,
./novaic-cortex/novaic_cortex/sandbox.py:26:    MountNamespaceLogicalFS,
./novaic-cortex/novaic_cortex/sandbox.py:54:    """Acquire LogicalFS view, run a process, release view, assemble ShellResult."""
./novaic-cortex/novaic_cortex/sandbox.py:58:        logical_fs: MountNamespaceLogicalFS,
./novaic-cortex/novaic_cortex/sandbox.py:92:        with tempfile.TemporaryDirectory(prefix="novaic-cortex-logicalfs-") as tmp:
./novaic-cortex/novaic_cortex/sandbox.py:156:    """Public shell facade backed by explicit LogicalFS and sandboxd SDK client."""
./novaic-cortex/novaic_cortex/sandbox.py:168:        self.logical_fs = MountNamespaceLogicalFS(
./novaic-cortex/novaic_cortex/sandbox.py:182:    def logical_fs_capabilities(self) -> LogicalFSCapabilities:
./scripts/ci/lint_deploy_fresh_smoke.py:42:        "novaic-logicalfs",
./docs/reference/blob-service.md:7:LogicalFS is the Cortex/shell realtime `RO` / `RW` authority above Blob. Blob
./docs/reference/blob-service.md:49:appears in `/ro` / `/rw`; those decisions belong to LogicalFS and Cortex.
./docs/reference/blob-service.md:51:first; LogicalFS does not expose display/download handles directly.
./docs/reference/blob-service.md:91:file semantics go through the LogicalFS/Cortex file authority boundary described
./docs/reference/blob-service.md:92:in `docs/architecture/logicalfs-realtime-file-authority.md`.
./docs/cortex-architecture.md:13:| LogicalFS、注册表、对象键 | [cortex/object-keys.md](cortex/object-keys.md) |
./docs/cortex-architecture.md:76:| `registry.py` | `WorkspaceRegistry`：按 user 缓存 LogicalFS Blob object adapter，按 `(user, agent)` 缓存 `Workspace(LogicalFS authority)` |
./novaic-logicalfs/README.md:1:# NovaIC LogicalFS
./novaic-logicalfs/README.md:3:Business-agnostic LogicalFS substrate.
./novaic-logicalfs/README.md:5:LogicalFS turns an explicit snapshot into a local filesystem view and turns RW
./novaic-logicalfs/README.md:6:view changes back into an explicit patch. It does not know Cortex, agents,
```

## logical-fs

- candidate_path_matches: 0
- launch_reference_matches: 0

### Candidate paths (first 30)

```text
```

### Launch references (first 30)

```text
```

## sandbox

- candidate_path_matches: 22
- launch_reference_matches: 476

### Candidate paths (first 30)

```text
docs/cortex/sandbox-shell.md
novaic-cortex/novaic_cortex/sandbox.py
novaic-cortex/tests/test_sandbox_requires_mount_namespace.py
novaic-cortex/tests/test_sandboxd_wiring.py
novaic-sandbox-sdk/README.md
novaic-sandbox-sdk/pyproject.toml
novaic-sandbox-sdk/sandbox_sdk/__init__.py
novaic-sandbox-sdk/sandbox_sdk/client.py
novaic-sandbox-sdk/sandbox_sdk/contracts.py
novaic-sandbox-sdk/sandbox_sdk/types.py
novaic-sandbox-sdk/tests/test_sandbox_sdk.py
novaic-sandbox-service/main_sandbox_service.py
novaic-sandbox-service/requirements.txt
novaic-sandbox-service/sandbox_service/__init__.py
novaic-sandbox-service/sandbox_service/core/__init__.py
novaic-sandbox-service/sandbox_service/core/filesystem.py
novaic-sandbox-service/sandbox_service/core/mount_namespace.py
novaic-sandbox-service/sandbox_service/core/process.py
novaic-sandbox-service/sandbox_service/main.py
novaic-sandbox-service/tests/test_sandbox_boundary.py
novaic-sandbox-service/tests/test_sandbox_core.py
novaic-sandbox-service/tests/test_sandbox_service.py
```

### Launch references (first 30)

```text
./scripts/start.sh:17:#   - Sandboxd       :19994  Generic sandbox process execution
./scripts/start.sh:18:#   - Cortex         :19996  Scope tree, LLM context assembly, Workspace, Sandbox
./scripts/start.sh:48:PORT_SANDBOXD=19994
./scripts/start.sh:58:SANDBOXD_URL="http://$HOST:$PORT_SANDBOXD"
./scripts/start.sh:138:    pkill -9 -f "main_sandbox_service.py" 2>/dev/null || true
./scripts/start.sh:140:    for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:151:for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:230:PYTHONPATH="$BASE/novaic-sandbox-sdk:$BASE/novaic-common:$BASE/novaic-sandbox-service:${PYTHONPATH:-}" \
./scripts/start.sh:231:$(py novaic-sandbox-service) "$BASE/novaic-sandbox-service/main_sandbox_service.py" \
./scripts/start.sh:232:    --host "$HOST" --port "$PORT_SANDBOXD" \
./scripts/start.sh:233:    >> "$LOG_DIR/sandboxd.log" 2>&1 &
./scripts/start.sh:234:wait_port "$PORT_SANDBOXD" "Sandboxd"
./scripts/start.sh:247:PYTHONPATH="$BASE/novaic-cortex:$BASE/novaic-logicalfs:$BASE/novaic-sandbox-sdk:$BASE/novaic-common:${PYTHONPATH:-}" \
./scripts/start.sh:253:	    --sandboxd-url "$SANDBOXD_URL" \
./novaic-sandbox-service/main_sandbox_service.py:2:"""Sandboxd service entry point."""
./novaic-sandbox-service/main_sandbox_service.py:19:from sandbox_service.main import main
./novaic-sandbox-service/main_sandbox_service.py:22:if __name__ == "__main__":
./novaic-sandbox-service/sandbox_service/main.py:1:"""Independent sandbox execution service."""
./novaic-sandbox-service/sandbox_service/main.py:5:import argparse
./novaic-sandbox-service/sandbox_service/main.py:10:from fastapi import FastAPI, HTTPException, Request
./novaic-sandbox-service/sandbox_service/main.py:12:from sandbox_sdk import (
./novaic-sandbox-service/sandbox_service/main.py:13:    SandboxExecResult,
./novaic-sandbox-service/sandbox_service/main.py:14:    SandboxdExecuteRequest,
./novaic-sandbox-service/sandbox_service/main.py:15:    SandboxdExecuteResponse,
./novaic-sandbox-service/sandbox_service/main.py:17:from sandbox_service.core.process import AsyncProcessRunner, BindMountPlan, ProcessRunResult, ProcessSpec
./novaic-sandbox-service/sandbox_service/main.py:19:logger = logging.getLogger("sandboxd")
./novaic-sandbox-service/sandbox_service/main.py:37:def _sdk_request_to_core_spec(request: SandboxdExecuteRequest) -> ProcessSpec:
./novaic-sandbox-service/sandbox_service/main.py:56:def _to_response(result: ProcessRunResult) -> SandboxdExecuteResponse:
./novaic-sandbox-service/sandbox_service/main.py:57:    return SandboxdExecuteResponse.from_result(
./novaic-sandbox-service/sandbox_service/main.py:58:        SandboxExecResult(
```

## sandboxd

- candidate_path_matches: 1
- launch_reference_matches: 176

### Candidate paths (first 30)

```text
novaic-cortex/tests/test_sandboxd_wiring.py
```

### Launch references (first 30)

```text
./scripts/start.sh:17:#   - Sandboxd       :19994  Generic sandbox process execution
./scripts/start.sh:48:PORT_SANDBOXD=19994
./scripts/start.sh:58:SANDBOXD_URL="http://$HOST:$PORT_SANDBOXD"
./scripts/start.sh:140:    for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:151:for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:232:    --host "$HOST" --port "$PORT_SANDBOXD" \
./scripts/start.sh:233:    >> "$LOG_DIR/sandboxd.log" 2>&1 &
./scripts/start.sh:234:wait_port "$PORT_SANDBOXD" "Sandboxd"
./scripts/start.sh:253:	    --sandboxd-url "$SANDBOXD_URL" \
./novaic-sandbox-service/main_sandbox_service.py:2:"""Sandboxd service entry point."""
./novaic-sandbox-service/sandbox_service/main.py:14:    SandboxdExecuteRequest,
./novaic-sandbox-service/sandbox_service/main.py:15:    SandboxdExecuteResponse,
./novaic-sandbox-service/sandbox_service/main.py:19:logger = logging.getLogger("sandboxd")
./novaic-sandbox-service/sandbox_service/main.py:37:def _sdk_request_to_core_spec(request: SandboxdExecuteRequest) -> ProcessSpec:
./novaic-sandbox-service/sandbox_service/main.py:56:def _to_response(result: ProcessRunResult) -> SandboxdExecuteResponse:
./novaic-sandbox-service/sandbox_service/main.py:57:    return SandboxdExecuteResponse.from_result(
./novaic-sandbox-service/sandbox_service/main.py:68:    app = FastAPI(title="NovaIC Sandboxd", version="1.0.0")
./novaic-sandbox-service/sandbox_service/main.py:76:            "service": "sandboxd",
./novaic-sandbox-service/sandbox_service/main.py:77:            "contract_version": "sandboxd/v1",
./novaic-sandbox-service/sandbox_service/main.py:86:            execute_request = SandboxdExecuteRequest.from_dict(payload)
./novaic-sandbox-service/sandbox_service/main.py:99:    parser = argparse.ArgumentParser(description="NovaIC sandboxd service")
./novaic-sandbox-service/sandbox_service/main.py:109:    logger.info("Starting sandboxd on %s:%s", args.host, args.port)
./novaic-sandbox-service/sandbox_service/__init__.py:1:"""NovaIC sandboxd service."""
./novaic-sandbox-service/sandbox_service/core/process.py:1:"""Async process execution substrate used inside sandboxd."""
./novaic-sandbox-service/sandbox_service/core/__init__.py:1:"""Sandboxd-internal execution substrate."""
./novaic-sandbox-service/sandbox_service/core/mount_namespace.py:1:"""Linux mount namespace helpers for sandboxd internals."""
./novaic-sandbox-sdk/sandbox_sdk/contracts.py:1:"""JSON wire contracts for sandboxd."""
./novaic-sandbox-sdk/sandbox_sdk/contracts.py:36:class SandboxdExecuteRequest:
./novaic-sandbox-sdk/sandbox_sdk/contracts.py:45:    def from_spec(cls, spec: SandboxExecSpec) -> "SandboxdExecuteRequest":
./novaic-sandbox-sdk/sandbox_sdk/contracts.py:56:    def from_dict(cls, data: Mapping[str, Any]) -> "SandboxdExecuteRequest":
```

## cortex

- candidate_path_matches: 169
- launch_reference_matches: 3799

### Candidate paths (first 30)

```text
docs/architecture/cortex.md
docs/cortex-architecture.md
docs/cortex/README.md
docs/cortex/agent-runtime-all-topics.md
docs/cortex/agent-runtime-cortex-call-chain.md
docs/cortex/architecture-review-2026-04-17.md
docs/cortex/boundary-contract.md
docs/cortex/budget-compact-algorithm.md
docs/cortex/builtin-tools-and-skills.md
docs/cortex/compactor-and-gem-fusion.md
docs/cortex/context-event-source.md
docs/cortex/context-event-write-cutover-map.md
docs/cortex/context-timeline-and-dfs.md
docs/cortex/deployment-and-startup.md
docs/cortex/design-doc-links.md
docs/cortex/engine-config-and-metrics.md
docs/cortex/extension-points.md
docs/cortex/hardening-checklist.md
docs/cortex/http-api.md
docs/cortex/internal-api-schemas.md
docs/cortex/invariants.md
docs/cortex/object-keys.md
docs/cortex/observability-and-tests.md
docs/cortex/recall.md
docs/cortex/runtime-facade.md
docs/cortex/sandbox-shell.md
docs/cortex/satellite-modules.md
docs/cortex/scope-lifecycle.md
docs/cortex/session-meta-json.md
docs/cortex/state-authority-implementation-plan.md
```

### Launch references (first 30)

```text
./README.md:15:├── novaic-cortex/               # Cortex scope / step 服务
./scripts/start.sh:18:#   - Cortex         :19996  Scope tree, LLM context assembly, Workspace, Sandbox
./scripts/start.sh:24:#   Workers → Cortex    (scope/context/shell APIs)
./scripts/start.sh:46:PORT_CORTEX=19996
./scripts/start.sh:60:CORTEX_URL="http://$HOST:$PORT_CORTEX"
./scripts/start.sh:139:    pkill -9 -f "main_cortex" 2>/dev/null || true
./scripts/start.sh:140:    for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:151:for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
./scripts/start.sh:179:CORTEX_INTERNAL_KEY=$(_cfg "['secrets']['cortex_internal_key']")
./scripts/start.sh:236:mkdir -p "$DATA_DIR/cortex"
./scripts/start.sh:239:# 127.0.0.1). Cortex refuses to start without a reachable Redis —
./scripts/start.sh:242:# ``novaic_cortex/scope_locks.py::RedisScopeLockManager``). Multi-worker /
./scripts/start.sh:243:# multi-replica Cortex is therefore always safe.
./scripts/start.sh:244:# Cortex runs out of its own venv; export PYTHONPATH so sibling infrastructure
./scripts/start.sh:246:CORTEX_BLOB_SERVICE_URL="$BLOB_URL" \
./scripts/start.sh:247:PYTHONPATH="$BASE/novaic-cortex:$BASE/novaic-logicalfs:$BASE/novaic-sandbox-sdk:$BASE/novaic-common:${PYTHONPATH:-}" \
./scripts/start.sh:248:$(py novaic-cortex) -m novaic_cortex.main_cortex \
./scripts/start.sh:249:    --host "$HOST" --port "$PORT_CORTEX" \
./scripts/start.sh:251:	    --internal-key "$CORTEX_INTERNAL_KEY" \
./scripts/start.sh:254:	    --cortex-api-url "$CORTEX_URL" \
./scripts/start.sh:255:	    --operational-sqlite-path "$DATA_DIR/cortex/operational.sqlite3" \
./scripts/start.sh:258:    >> "$LOG_DIR/cortex.log" 2>&1 &
./scripts/start.sh:259:wait_port "$PORT_CORTEX" "Cortex"
./scripts/start.sh:265:TASK_WORKER_ARGS="--business-url $BIZ_URL --queue-service-url $QS_URL --cortex-url $CORTEX_URL --data-dir $DATA_DIR"
./scripts/start.sh:266:SAGA_WORKER_ARGS="--queue-service-url $QS_URL --cortex-url $CORTEX_URL --data-dir $DATA_DIR"
./scripts/start.sh:267:SCHEDULER_ARGS="--business-url $BIZ_URL --queue-service-url $QS_URL --cortex-url $CORTEX_URL --data-dir $DATA_DIR"
./novaic-device/device/agent_vm_proxy.py:4:These routes are called by Cortex/Tools for device operations on agents:
./novaic-cortex/scripts/check_cortex_boundary.py:2:"""PR-76 Cortex boundary guard.
./novaic-cortex/scripts/check_cortex_boundary.py:4:The guard scans active Cortex Python source for concepts that no longer
./novaic-cortex/scripts/check_cortex_boundary.py:5:belong in Cortex. Documentation, ticket history, and tombstones are not
```

## gateway

- candidate_path_matches: 79
- launch_reference_matches: 1935

### Candidate paths (first 30)

```text
docs/architecture/gateway-decomposition-roadmap.md
docs/architecture/gateway-v2-target-architecture.md
docs/entangled/gateway-integration.md
docs/gateway-architecture.md
docs/gateway/README.md
docs/gateway/app-ws-and-signaling.md
docs/gateway/cloudbridge-vm.md
docs/gateway/db-v63-split.md
docs/gateway/entangled-hooks.md
docs/gateway/internal-and-workers.md
docs/gateway/rest-auth-and-deps.md
docs/roadmap/gateway-decomposition.md
docs/roadmap/gateway_v2_checklist.md
docs/roadmap/tickets/PR-104-gateway-entangled-endpoint-only.md
docs/roadmap/tickets/PR-121-gateway-entangled-sync-discovery-boundary.md
docs/roadmap/tickets/PR-152-gateway-business-entangled-boundary-review.md
docs/roadmap/tickets/PR-152A-remove-gateway-startup-business-state.md
docs/roadmap/tickets/PR-152B-replace-gateway-generic-business-entity-client.md
docs/roadmap/tickets/PR-157-app-gateway-vm-http-residue-review.md
docs/roadmap/tickets/PR-157B-remove-app-gateway-vm-service.md
docs/roadmap/tickets/PR-157D-guard-app-gateway-vm-http-residue.md
docs/roadmap/tickets/PR-161C-delete-gateway-legacy-data-replayer-scripts.md
docs/roadmap/tickets/PR-183-gateway-auth-file-proxy-boundary-cleanup.md
docs/roadmap/tickets/PR-183A-gateway-auth-token-transport-tightening.md
docs/roadmap/tickets/PR-183B-gateway-file-proxy-file-id-boundary.md
docs/roadmap/tickets/PR-196-runtime-queue-gateway-centric-doc-cleanup.md
docs/roadmap/tickets/PR-197-gateway-entangled-boundary-doc-cleanup.md
docs/roadmap/tickets/PR-197A-gateway-readme-boundary.md
docs/roadmap/tickets/PR-203-app-gateway-blob-attachment-access.md
novaic-app/src-tauri/gen/apple/assets/backends/novaic-gateway
```

### Launch references (first 30)

```text
./novaic-device/device/config_agents_db.py:28:GATEWAY_PORT = 19999
./novaic-device/device/gateway_signaling.py:1:"""Push WebRTC signaling events to the user's App WS via Business Service.
./novaic-device/device/gateway_signaling.py:3:Return path: VmControl → Device Service → Business → Gateway → App WS.
./novaic-device/device/gateway_signaling.py:15:    user_id: str, device_id: str, session_id: str, candidate: dict,
./novaic-device/device/gateway_signaling.py:17:    """Push ICE candidate to App via Business → Gateway."""
./novaic-device/device/gateway_signaling.py:18:    await _push_via_business(user_id, "ice_candidate", {
./novaic-device/device/gateway_signaling.py:19:        "device_id": device_id,
./novaic-device/device/gateway_signaling.py:26:    user_id: str, device_id: str, session_id: str, sdp_answer: str,
./novaic-device/device/gateway_signaling.py:28:    """Push WebRTC SDP answer to App via Business → Gateway."""
./novaic-device/device/gateway_signaling.py:29:    await _push_via_business(user_id, "webrtc_answer", {
./novaic-device/device/gateway_signaling.py:30:        "device_id": device_id,
./novaic-device/device/gateway_signaling.py:36:async def _push_via_business(user_id: str, event_type: str, payload: dict) -> None:
./novaic-device/device/gateway_signaling.py:37:    """Send a push event through Business Service's signaling relay."""
./novaic-device/device/gateway_signaling.py:38:    biz_url = getattr(ServiceConfig, "BUSINESS_URL", "http://127.0.0.1:19998").rstrip("/")
./novaic-device/device/gateway_signaling.py:41:        async with internal_async_client(service_name="device", timeout=10.0) as client:
./novaic-device/device/gateway_signaling.py:48:                logger.warning("[Signaling] Business push failed: %d %s", resp.status_code, resp.text[:200])
./novaic-device/device/gateway_signaling.py:50:        logger.warning("[Signaling] Business push error: %s", e)
./novaic-device/device/gateway_facing_api.py:2:HTTP APIs exposed by Device Service for Gateway to call.
./novaic-device/device/gateway_facing_api.py:4:Gateway should NEVER import device.* Python modules directly.
./novaic-device/device/gateway_facing_api.py:5:Instead, Gateway calls these HTTP endpoints when it needs device-domain info.
./novaic-device/device/gateway_facing_api.py:8:Device Service does not run local QEMU or VNC.
./novaic-device/device/gateway_facing_api.py:11:  GET  /internal/device-registry/connected?user_id=...   → list connected devices
./novaic-device/device/gateway_facing_api.py:12:  GET  /internal/device-registry/device/{device_id}      → get device state
./novaic-device/device/gateway_facing_api.py:13:  POST /internal/device-registry/push-to-device           → send push msg to device
./novaic-device/device/gateway_facing_api.py:27:from fastapi import APIRouter, HTTPException
./novaic-device/device/gateway_facing_api.py:35:# ── Device Registry queries ──────────────────────────────────────────────────
./novaic-device/device/gateway_facing_api.py:37:@router.get("/device-registry/connected")
./novaic-device/device/gateway_facing_api.py:38:async def list_connected_devices(user_id: str = ""):
./novaic-device/device/gateway_facing_api.py:39:    from device.pc_client import get_device_registry
./novaic-device/device/gateway_facing_api.py:40:    registry = get_device_registry()
```

## business

- candidate_path_matches: 102
- launch_reference_matches: 3417

### Candidate paths (first 30)

```text
docs/roadmap/tickets/PR-07-business-agent-owner-endpoint.md
docs/roadmap/tickets/PR-11-business-trigger-to-assembler.md
docs/roadmap/tickets/PR-111-business-owned-system-prompt.md
docs/roadmap/tickets/PR-112-retire-runtime-business-client-legacy-wrappers.md
docs/roadmap/tickets/PR-115-remove-business-unread-zombie-routes.md
docs/roadmap/tickets/PR-117-remove-business-taskmanager-legacy-proxy.md
docs/roadmap/tickets/PR-149-retire-business-notebook-task-drive-surfaces.md
docs/roadmap/tickets/PR-152-gateway-business-entangled-boundary-review.md
docs/roadmap/tickets/PR-152A-remove-gateway-startup-business-state.md
docs/roadmap/tickets/PR-152B-replace-gateway-generic-business-entity-client.md
docs/roadmap/tickets/PR-159-business-product-context-boundary-review.md
docs/roadmap/tickets/PR-159A-business-product-context-boundary-guardrail.md
docs/roadmap/tickets/PR-169A-business-activity-timeline-action.md
docs/roadmap/tickets/PR-180-business-device-proxy-route-boundary-review.md
docs/roadmap/tickets/PR-180A-delete-business-device-proxy-routes.md
docs/roadmap/tickets/PR-182A-delete-legacy-business-health-stubs.md
docs/roadmap/tickets/PR-186B-business-environment-notification-hot-path.md
docs/roadmap/tickets/PR-188A-business-activity-timeline-main-subagent-resolution.md
docs/roadmap/tickets/PR-188A-business-activity-timeline-participants.md
docs/roadmap/tickets/PR-228-business-subagent-state-authority-cleanup.md
docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md
docs/roadmap/tickets/PR-75-remove-cortex-business-proxy-memory-task.md
novaic-agent-runtime/task_queue/business/__init__.py
novaic-agent-runtime/task_queue/business/llm.py
novaic-agent-runtime/tests/test_pr112_business_client_boundary.py
novaic-agent-runtime/tests/test_pr338_business_handlers_lifecycle_free.py
novaic-business/business/__init__.py
novaic-business/business/action_deps.py
novaic-business/business/agent_actions.py
novaic-business/business/api_key_actions.py
```

### Launch references (first 30)

```text
./novaic-device/device/gateway_signaling.py:1:"""Push WebRTC signaling events to the user's App WS via Business Service.
./novaic-device/device/gateway_signaling.py:3:Return path: VmControl → Device Service → Business → Gateway → App WS.
./novaic-device/device/gateway_signaling.py:17:    """Push ICE candidate to App via Business → Gateway."""
./novaic-device/device/gateway_signaling.py:18:    await _push_via_business(user_id, "ice_candidate", {
./novaic-device/device/gateway_signaling.py:28:    """Push WebRTC SDP answer to App via Business → Gateway."""
./novaic-device/device/gateway_signaling.py:29:    await _push_via_business(user_id, "webrtc_answer", {
./novaic-device/device/gateway_signaling.py:36:async def _push_via_business(user_id: str, event_type: str, payload: dict) -> None:
./novaic-device/device/gateway_signaling.py:37:    """Send a push event through Business Service's signaling relay."""
./novaic-device/device/gateway_signaling.py:38:    biz_url = getattr(ServiceConfig, "BUSINESS_URL", "http://127.0.0.1:19998").rstrip("/")
./novaic-device/device/gateway_signaling.py:48:                logger.warning("[Signaling] Business push failed: %d %s", resp.status_code, resp.text[:200])
./novaic-device/device/gateway_signaling.py:50:        logger.warning("[Signaling] Business push error: %s", e)
./novaic-device/main_device.py:24:    _parser.add_argument("--business-url", default="http://127.0.0.1:19998", help="Business Service URL")
./novaic-device/main_device.py:36:    ServiceConfig.BUSINESS_URL = _cli_args.business_url
./novaic-device/main_device.py:105:    push_device_schemas(ServiceConfig.BUSINESS_URL, service_token=_svc_token)
./novaic-device/main_device.py:106:    logger.info("Device entity schemas pushed via Business proxy")
./novaic-device/device/entity_store.py:2:Device Service Entity Store — all entity CRUD routed through Business Service.
./novaic-device/device/entity_store.py:4:Previously talked to Entangled directly; now delegates to Business
./novaic-device/device/entity_store.py:5:/internal/entities/* so Business is the single Entangled gateway.
./novaic-device/device/entity_store.py:12:from device.business_entity_client import BusinessEntityClient
./novaic-device/device/entity_store.py:14:_store: Optional[BusinessEntityClient] = None
./novaic-device/device/entity_store.py:17:def get_entity_store() -> BusinessEntityClient:
./novaic-device/device/entity_store.py:20:        _store = BusinessEntityClient()
./novaic-device/device/business_entity_client.py:2:Device-side entity client — routes ALL entity CRUD through Business Service
./novaic-device/device/business_entity_client.py:5:Drop-in replacement for the old DeviceEntityStore; same public interface.
./novaic-device/device/business_entity_client.py:7:Protocol mapping (Business proxy → Entangled):
./novaic-device/device/business_entity_client.py:22:from device.contracts import BusinessEntityProxyRequest, EntityRequestScope
./novaic-device/device/business_entity_client.py:27:class BusinessEntityClient:
./novaic-device/device/business_entity_client.py:28:    """Entity CRUD via Business Service HTTP proxy."""
./novaic-device/device/business_entity_client.py:30:    def __init__(self, business_url: Optional[str] = None, *, timeout: float = 30.0):
./novaic-device/device/business_entity_client.py:32:            business_url
```

## device

- candidate_path_matches: 64
- launch_reference_matches: 5491

### Candidate paths (first 30)

```text
docs/roadmap/tickets/PR-106-host-desktop-device-status-closure.md
docs/roadmap/tickets/PR-120-remove-device-entangled-cli.md
docs/roadmap/tickets/PR-151-remove-device-binding-legacy-compat.md
docs/roadmap/tickets/PR-157A-device-entangled-vm-prep-actions.md
docs/roadmap/tickets/PR-180-business-device-proxy-route-boundary-review.md
docs/roadmap/tickets/PR-180A-delete-business-device-proxy-routes.md
docs/roadmap/tickets/PR-185-app-device-vm-historical-naming-cleanup.md
docs/roadmap/tickets/PR-185A-rename-device-vnc-target-hook.md
docs/roadmap/tickets/PR-185B-remove-use-devices-legacy-sync-helpers.md
novaic-app/src-tauri/resources/android-sdk/emulator/lib/emulated_bluetooth_device.proto
novaic-app/src-tauri/src/platform/device_info.rs
novaic-app/src-tauri/vmcontrol/src/db/device_repo.rs
novaic-app/src/application/deviceService.test.ts
novaic-app/src/application/deviceService.ts
novaic-app/src/components/Console/DeviceConsole.tsx
novaic-app/src/components/Layout/DeviceFloatingPanel.tsx
novaic-app/src/components/Layout/DeviceSidebar.tsx
novaic-app/src/components/Layout/PcClientDeviceList.tsx
novaic-app/src/components/VM/DeviceManagerModal.tsx
novaic-app/src/components/VM/DeviceManagerPage.tsx
novaic-app/src/components/Visual/DeviceVNCView.tsx
novaic-app/src/components/hooks/useDevices.ts
novaic-app/src/data/entities/devices.ts
novaic-app/src/hooks/useDeviceStatus.ts
novaic-app/src/hooks/useDeviceStatusPolling.test.ts
novaic-app/src/hooks/useDeviceStatusPolling.ts
novaic-app/src/hooks/useDeviceTarget.ts
novaic-app/src/stores/deviceStatusStore.ts
novaic-app/src/utils/deviceStatusKey.ts
novaic-app/strip_lines_device_fp.py
```

### Launch references (first 30)

```text
./novaic-device/device/config_agents_db.py:22:from device.db_access import get_db
./novaic-device/device/config_agents_db.py:24:from device.entity_store import get_entity_store
./novaic-device/device/config_agents_db.py:28:GATEWAY_PORT = 19999
./novaic-device/device/config_agents_db.py:29:BASE_PORT = 20000
./novaic-device/device/config_agents_db.py:30:BASE_VMUSE_PORT = 18000
./novaic-device/device/config_agents_db.py:55:    device_serial: str = ""      # e.g., emulator-5554
./novaic-device/device/config_agents_db.py:83:    # New unified devices list (v38)
./novaic-device/device/config_agents_db.py:84:    # Will be populated from devices table when loading agent
./novaic-device/device/config_agents_db.py:85:    devices: List[Any] = Field(default_factory=list)
./novaic-device/device/config_agents_db.py:88:def get_agent_port(agent_index: int, service: str) -> int:
./novaic-device/device/config_agents_db.py:102:        return BASE_PORT + agent_index
./novaic-device/device/config_agents_db.py:104:        return BASE_VMUSE_PORT + agent_index
./novaic-device/device/config_agents_db.py:106:        base = BASE_PORT + agent_index * PORTS_PER_AGENT
./novaic-device/device/config_agents_db.py:110:def allocate_ports_for_agent(agent_index: int) -> PortConfig:
./novaic-device/device/config_agents_db.py:119:        ssh=get_agent_port(agent_index, "ssh"),
./novaic-device/device/config_agents_db.py:120:        vmuse=get_agent_port(agent_index, "vmuse"),
./novaic-device/device/config_agents_db.py:153:    def _load_devices_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
./novaic-device/device/config_agents_db.py:154:        """Load devices from devices table for an agent (v38).
./novaic-device/device/config_agents_db.py:156:        DeviceRepository was removed; query via EntityStore instead.
./novaic-device/device/config_agents_db.py:159:            rows = self.store.list("devices", "", params={"agent_id": agent_id})
./novaic-device/device/config_agents_db.py:162:            logger.warning(f"[AgentConfigManagerDB] Failed to load devices for agent {agent_id}: {e}")
./novaic-device/device/config_agents_db.py:169:    def _allocate_new_ports(self) -> PortConfig:
./novaic-device/device/config_agents_db.py:178:        used_ssh_ports = set()
./novaic-device/device/config_agents_db.py:179:        used_vmuse_ports = set()
./novaic-device/device/config_agents_db.py:184:                    used_ssh_ports.add(ports["ssh"])
./novaic-device/device/config_agents_db.py:186:                    used_vmuse_ports.add(ports["vmuse"])
./novaic-device/device/config_agents_db.py:188:        logger.info(f"[_allocate_new_ports] Used SSH ports: {sorted(used_ssh_ports)}")
./novaic-device/device/config_agents_db.py:189:        logger.info(f"[_allocate_new_ports] Used VMUSE ports: {sorted(used_vmuse_ports)}")
./novaic-device/device/config_agents_db.py:193:            ssh_port = BASE_PORT + offset
./novaic-device/device/config_agents_db.py:194:            vmuse_port = BASE_VMUSE_PORT + offset
```

## devicectl

- candidate_path_matches: 0
- launch_reference_matches: 65

### Candidate paths (first 30)

```text
```

### Launch references (first 30)

```text
./examples/tauri-ios-hello/scripts/build-and-install-ios.sh:5:# This script uses "tauri ios build" + devicectl install.
./examples/tauri-ios-hello/scripts/build-and-install-ios.sh:27:DEVICE=$(xcrun devicectl list devices 2>/dev/null | awk '
./examples/tauri-ios-hello/scripts/build-and-install-ios.sh:40:xcrun devicectl device install app --device "$DEVICE" "$IPA_PATH"
./examples/tauri-ios-hello/README.md:30:If `tauri ios run` fails with "Couldn't load -exportOptionsPlist", use the script above instead (it uses `tauri ios build` + `devicectl install`).
./byclaw-website/src/App.tsx:33:            <a href="#" className="btn btn-secondary" onClick={(e) => { e.preventDefault(); alert("iOS app requires TestFlight or devicectl deployment."); }}>
./docs/architecture/agent-pipeline.md:56:     → devicectl hd ... → Business → Device
./novaic-cortex/novaic_cortex/shell_capabilities.py:4:LogicalFS view (agentctl, cortex, devicectl) and the explicit environment keys
./novaic-cortex/novaic_cortex/shell_capabilities.py:14:_CAPABILITY_COMMANDS = ("agentctl", "cortex", "devicectl")
./novaic-cortex/novaic_cortex/shell_capabilities.py:73:    "devicectl": \"\"\"devicectl - mounted device command surface inside the Cortex shell
./novaic-cortex/novaic_cortex/shell_capabilities.py:76:  devicectl --help
./novaic-cortex/novaic_cortex/shell_capabilities.py:77:  devicectl hd screenshot
./novaic-cortex/novaic_cortex/shell_capabilities.py:78:  devicectl hd shell-exec --command TEXT [--timeout N]
./novaic-cortex/novaic_cortex/shell_capabilities.py:79:  devicectl hd mouse --json JSON
./novaic-cortex/novaic_cortex/shell_capabilities.py:80:  devicectl hd keyboard --json JSON
./novaic-cortex/novaic_cortex/shell_capabilities.py:81:  devicectl hd clipboard-get
./novaic-cortex/novaic_cortex/shell_capabilities.py:82:  devicectl hd clipboard-set --json JSON
./novaic-cortex/novaic_cortex/shell_capabilities.py:83:  devicectl hd file-pull --json JSON
./novaic-cortex/novaic_cortex/shell_capabilities.py:84:  devicectl hd file-push --json JSON
./novaic-cortex/novaic_cortex/shell_capabilities.py:85:  devicectl hd <command> --json-file PATH
./novaic-cortex/novaic_cortex/shell_capabilities.py:342:        source_ref="devicectl hd screenshot",
./novaic-cortex/novaic_cortex/shell_capabilities.py:358:            "tool": "devicectl hd screenshot",
./novaic-cortex/novaic_cortex/shell_capabilities.py:388:        source_ref=f"devicectl hd file-pull {{path}}".strip(),
./novaic-cortex/novaic_cortex/shell_capabilities.py:401:        source={{"tool": "devicectl hd file-pull", "path": path}},
./novaic-cortex/novaic_cortex/shell_capabilities.py:880:def _devicectl_hd(args: list[str]) -> None:
./novaic-cortex/novaic_cortex/shell_capabilities.py:882:        print(HELP["devicectl"].rstrip())
./novaic-cortex/novaic_cortex/shell_capabilities.py:912:def _devicectl(args: list[str]) -> None:
./novaic-cortex/novaic_cortex/shell_capabilities.py:914:        print(HELP["devicectl"].rstrip())
./novaic-cortex/novaic_cortex/shell_capabilities.py:917:        _devicectl_hd(args[1:])
./novaic-cortex/novaic_cortex/shell_capabilities.py:1039:    if COMMAND == "devicectl":
./novaic-cortex/novaic_cortex/shell_capabilities.py:1040:        _devicectl(args)
```

## agentctl

- candidate_path_matches: 0
- launch_reference_matches: 212

### Candidate paths (first 30)

```text
```

### Launch references (first 30)

```text
./scripts/ci/lint_agent_main_path_acceptance.sh:34:  rg -q 'agentctl im read --notification-id' novaic-agent-runtime/task_queue/handlers/context_handlers.py
./novaic-app/src/components/Visual/ActivityTimeline.tsx:36:const AGENTCTL_IM_READ_PATTERN = /\bagentctl\s+im\s+read\b/i;
./novaic-app/src/components/Visual/ActivityTimeline.tsx:37:const AGENTCTL_IM_REPLY_PATTERN = /\bagentctl\s+im\s+reply\b/i;
./novaic-app/src/components/Visual/ActivityTimeline.tsx:58:function isAgentctlImReadRecord(record: ActivityTimelineRecord): boolean {
./novaic-app/src/components/Visual/ActivityTimeline.tsx:59:  return normalizedTool(record) === 'shell' && AGENTCTL_IM_READ_PATTERN.test(recordSearchText(record));
./novaic-app/src/components/Visual/ActivityTimeline.tsx:62:function isAgentctlImReplyRecord(record: ActivityTimelineRecord): boolean {
./novaic-app/src/components/Visual/ActivityTimeline.tsx:63:  return normalizedTool(record) === 'shell' && AGENTCTL_IM_REPLY_PATTERN.test(recordSearchText(record));
./novaic-app/src/components/Visual/ActivityTimeline.tsx:69:  if (isAgentctlImReadRecord(record)) return '读取了你的消息';
./novaic-app/src/components/Visual/ActivityTimeline.tsx:70:  if (isAgentctlImReplyRecord(record)) return '已回复你';
./novaic-app/src/components/Visual/ActivityTimeline.tsx:75:      AGENTCTL_IM_READ_PATTERN.test(reasoningText) ||
./novaic-app/src/components/Visual/ActivityTimeline.tsx:81:    if (AGENTCTL_IM_REPLY_PATTERN.test(reasoningText) || reasoningText.includes('回复')) {
./novaic-app/src/components/Visual/ActivityTimeline.acceptance.test.tsx:34:            text: 'agentctl im reply --message-file /cortex/rw/reply.md',
./novaic-app/src/components/Visual/ActivityTimeline.acceptance.test.tsx:41:            title: 'agentctl im reply 完成',
./novaic-app/src/components/Visual/ActivityTimeline.acceptance.test.tsx:63:    expect(screen.queryByText(/agentctl im reply/i)).toBeNull();
./novaic-app/src/components/Visual/ActivityTimeline.test.tsx:28:            text: 'agentctl im reply --message-file /cortex/rw/reply.md',
./novaic-app/src/components/Visual/ActivityTimeline.test.tsx:34:            title: 'agentctl im reply 完成',
./novaic-app/src/components/Visual/ActivityTimeline.test.tsx:47:    expect(screen.queryByText('agentctl im reply')).toBeNull();
./novaic-app/src/components/Visual/ActivityTimeline.test.tsx:68:            text: 'agentctl im read --notification-id msg_123',
./novaic-app/src/components/Visual/ActivityTimeline.test.tsx:74:            title: 'agentctl im read 完成',
./novaic-app/src/components/Visual/ActivityTimeline.test.tsx:110:    expect(screen.queryByText('agentctl im read')).toBeNull();
./docs/cortex-architecture.md:44:1. LLM 先通过 shell 执行 `agentctl im reply` 回复用户。
./novaic-logicalfs/README.md:7:subagents, agentctl, or process execution.
./novaic-cortex/novaic_cortex/context_event_projection.py:338:            f'Use shell(command="agentctl im read --notification-id {notification_id}") '
./novaic-app/src/components/hooks/useActivityTimeline.test.ts:115:          text: 'agentctl im reply --message-file /cortex/rw/reply.md',
./novaic-app/src/components/hooks/useActivityTimeline.test.ts:229:          text: 'agentctl im reply --message-file /cortex/rw/reply.md',
./docs/architecture/service-topology.md:114:   → shell executes `agentctl im reply` to write the user-visible message through Business/Environment projection
./novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py:392:- For long-running commands (>30s), use a host-provided background task; in NovaIC shell, use agentctl subagent spawn
./novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py:395:NovaIC shell example: agentctl subagent spawn --task "Run: npm run build"
./docs/architecture/agent-pipeline.md:53:     → agentctl im reply/send/read/history/search/context → Business Environment APIs
./docs/architecture/agent-pipeline.md:54:     → agentctl subagent spawn / media audio-qa → Business/SubAgent/Runtime APIs
```
