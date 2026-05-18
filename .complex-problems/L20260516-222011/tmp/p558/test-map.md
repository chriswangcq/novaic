# P558 LogicalFS / Sandbox / Blob Entry Points And Tests Map

## Scope

This map covers the active layering chain:

- Cortex service and tool shell entrypoints.
- Cortex `MountNamespaceLogicalFS` adapter over the generic LogicalFS substrate.
- Sandbox service / SDK process execution boundary.
- Blob service byte/object APIs.
- Agent runtime shell/display/tool-output projection boundary.

## Entrypoint Map

### Cortex Service And Shell

- `novaic-cortex/novaic_cortex/main_cortex.py`
  - Requires `--blob-service-url`, `--sandboxd-url`, `--operational-sqlite-path`, and `--redis-url`.
  - Wires `SandboxdClient` into Cortex through `set_sandbox_process_runner_factory`.
- `novaic-cortex/novaic_cortex/api.py`
  - `/v1/shell` builds a `Cortex`, initializes it, and calls `Cortex.tool_shell`.
- `novaic-cortex/novaic_cortex/runtime.py`
  - `Cortex.tool_shell` delegates to `Sandbox.exec`.
  - No local shell fallback is visible in this path.
- `novaic-cortex/novaic_cortex/sandbox.py`
  - `ShellExecutionOrchestrator` acquires a LogicalFS view, asks sandboxd to execute, releases the view, then returns terminal text and changed files.
  - Commands that reuse leaked `novaic-cortex-sandbox-*` backing paths are rejected.

### Cortex LogicalFS Adapter

- `novaic-cortex/novaic_cortex/logical_fs.py`
  - `MountNamespaceLogicalFS` projects a bounded workspace snapshot into `/cortex/ro` and `/cortex/rw`.
  - RO materialization is intentionally bounded to config plus the current root/wake scope.
  - RW materialization includes root files, `/rw/public`, `/rw/system`, and current subagent workspace.
  - RW changes are observed as a LogicalFS patch and written back through the Workspace logical path boundary.

### Sandbox Service / SDK

- `novaic-sandbox-service/sandbox_service/main.py`
  - Exposes `/v1/execute`.
  - Validates cwd and bind mount metadata.
  - Runs `AsyncProcessRunner` over a `ProcessSpec`.
- `novaic-sandbox-sdk/sandbox_sdk/client.py`
  - Sends `SandboxdExecuteRequest` to sandboxd.
- `novaic-sandbox-sdk/sandbox_sdk/contracts.py`
  - Encodes sandboxd stdout/stderr as base64 on the service wire only.
  - The SDK decodes this back to bytes before Cortex assembles shell text.

### Blob Service And LogicalFS Object Store

- `novaic-blob-service/blob_service/main.py`
  - Creates Blob Service as a standalone FastAPI server.
  - Requires an explicit data directory.
- `novaic-blob-service/blob_service/routes.py`
  - Provides `/v1/blobs` upload/get/presign/delete APIs.
  - Provides `/v1/objects` APIs used by LogicalFS object-store adapters.
- `novaic-logicalfs/logicalfs/blob_store.py`
  - `BlobObjectStore` is explicitly documented as below LogicalFS, not as semantic workspace authority.
- `novaic-logicalfs/logicalfs/local.py`
  - `LocalLogicalFSProvider` materializes explicit snapshots and observes RW patches.

### Runtime Tool Output / Display

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `shell` executor routes through Cortex bridge and returns `tool-output.v1` terminal text with bounded stdout/stderr previews.
  - Full shell raw output is stored as durable payload rather than public LLM text.
  - `display` downloads a blob and returns image/text content for explicit perception.
  - Display public output is sanitized so image bytes do not remain in public tool history.
- `novaic-cortex/novaic_cortex/step_result_projection.py`
  - Historical and current non-display tool output are manifest/text only.
  - Explicit `display_perception` may include visual content.
- `novaic-agent-runtime/task_queue/utils/context.py`
  - Only current-turn `display_perception` tool messages may be converted into provider-native image messages.
  - Shell and historical tool messages remain text receipts.

## Focused Test Map

### Cortex

- LogicalFS/sandbox wiring:
  - `novaic-cortex/tests/test_sandboxd_wiring.py`
  - `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`
  - `novaic-cortex/tests/test_workspace_materialize.py`
  - `novaic-cortex/tests/test_workspace_authority.py`
- Blob and artifact projection:
  - `novaic-cortex/tests/test_blob_boundary_guard.py`
  - `novaic-cortex/tests/test_blob_payload_client.py`
  - `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`
  - `novaic-cortex/tests/test_tool_output_projection.py`
  - `novaic-cortex/tests/test_step_result_projection.py`
- Event/read model authority:
  - `novaic-cortex/tests/test_context_event_read_source_guards.py`
  - `novaic-cortex/tests/test_context_event_write_authority.py`
  - `novaic-cortex/tests/test_context_event_store.py`

### LogicalFS

- `novaic-logicalfs/tests/test_logicalfs.py`
- `novaic-logicalfs/tests/test_authority.py`
- `novaic-logicalfs/tests/test_blob_store.py`

### Sandbox Service / SDK

- `novaic-sandbox-service/tests/test_sandbox_service.py`
- `novaic-sandbox-service/tests/test_sandbox_core.py`
- `novaic-sandbox-service/tests/test_sandbox_boundary.py`
- `novaic-sandbox-sdk/tests/test_sandbox_sdk.py`

### Blob Service

- `novaic-blob-service/tests/test_blob_service.py`
- `novaic-blob-service/tests/test_backends.py`

### Agent Runtime

- Shell/display/tool-output:
  - `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
- Cortex dependency boundary:
  - `novaic-agent-runtime/tests/test_pr147_cortex_required.py`
  - `novaic-agent-runtime/tests/test_runtime_tool_path_contract.py`

## Coverage Gaps To Carry Forward

- P553 should classify whether `Workspace.materialize()` is only historical naming/API residue or an active semantic leak.
- P553 should keep `BlobObjectStore` under scrutiny: it is currently documented as below LogicalFS, but the audit must verify callers do not use it as a workspace authority bypass.
- P555 should run the focused test subset across Cortex, LogicalFS, sandbox, blob, and runtime after P553/P554 finish.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p558/entrypoint-files.txt`
- `.complex-problems/L20260516-222011/tmp/p558/test-files.txt`
- `.complex-problems/L20260516-222011/tmp/p558/entrypoint-slices.txt`
