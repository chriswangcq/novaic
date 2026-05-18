# Cortex Boundary Map

## Role
Cortex is the semantic state/context/scope service. It owns the agent work trace semantics: scope lifecycle, context event append/replay/projection, active stack projection, payload manifests, tool schema surfaces, and shell capability orchestration.

Cortex does **not** own foundational byte storage, realtime file authority, or process execution:
- Blob Service owns byte/object storage and artifact transport.
- LogicalFS owns realtime logical RO/RW file authority semantics as a substrate/library today.
- Sandboxd owns process execution; Cortex calls sandboxd through `sandbox_sdk`.
- Queue/Runtime own session/wake/worker orchestration and call Cortex through HTTP topics.

## Entrypoints and Launch Evidence
- `novaic-cortex/novaic_cortex/main_cortex.py`: CLI/uvicorn entrypoint for Cortex HTTP service.
- `novaic-cortex/novaic_cortex/api.py`: FastAPI app `NovAIC Cortex`, version `0.2.0`, exposing agent tool, CLI, and internal context/scope APIs.
- `novaic-cortex/novaic_cortex/cli.py`: Cortex CLI helper entrypoint.
- `novaic-cortex/novaic_cortex/shell_capabilities.py`: shell-side capability CLI entrypoint exposed through sandbox shell.
- `scripts/start.sh`: launches `python -m novaic_cortex.main_cortex` with explicit `--blob-service-url`, `--sandboxd-url`, `--cortex-api-url`, `--operational-sqlite-path`, and `--redis-url`.
- `novaic-app/scripts/start-backends.sh` and generated app resource copies reference the Cortex URL and worker `--cortex-url` arguments.

## Semantic State Ownership
- `context_event_store.py`: append-only workspace-backed context event log for root-scope streams.
- `context_event_read_model.py`, `context_event_projection.py`, `context_event_writer.py`: event projection/read/write semantics.
- `scope_state.py`, `active_stack_projection.py`, `scope_transition_events.py`: scope lifecycle/projection semantics.
- `operational_store.py`: SQLite-backed durable control-plane state for scope lifecycle events, active-stack projections, and semantic manifests.
- `workspace.py`: workspace semantic file/package operations used by Cortex; foundational file authority below this is LogicalFS/Blob.

## Foundational Dependencies
- Blob dependency is explicit at startup: `main_cortex.py --blob-service-url` and registry wiring; the CLI help says Cortex never talks to a physical object store directly.
- Sandboxd dependency is explicit at startup: `main_cortex.py --sandboxd-url`; `sandbox.py` requires `SandboxdClient` execution and rejects missing sandbox executor instead of local fallback.
- LogicalFS is consumed through `logical_fs.py` and `workspace_authority.py` to build stable `/cortex/ro` and `/cortex/rw` views, not as Cortex-owned physical storage.
- Redis is mandatory for distributed scope locks via `main_cortex.py --redis-url` and `scope_locks.py`.
- Operational SQLite is mandatory for durable Cortex operational projections via `main_cortex.py --operational-sqlite-path`.

## Queue/Runtime Boundary
Runtime and queue workers pass `--cortex-url` and call Cortex HTTP endpoints for context/scope/prepare operations. Cortex does not decide wake/session scheduling; it serves context/scope state and shell orchestration APIs to Runtime.

## Active vs Generated/Historical Notes
- Active launch files: `scripts/start.sh`, `novaic-app/scripts/start-backends.sh`, `novaic-app/src-tauri/resources/backends/start-backends.sh`, and generated app resource copies.
- Current docs: `docs/architecture/cortex.md`, `docs/cortex/deployment-and-startup.md`, `docs/reference/config-and-environment.md`, `docs/architecture/data-ownership.md`.
- Historical/roadmap docs contain older Cortex architecture review/ticket material and should not be treated as active implementation truth without status banners.

## Potential P711 Cleanup Candidates
- `scripts/start.sh:18` still says `Cortex :19996 Scope tree, LLM context assembly, Workspace, Sandbox`. This compresses Sandbox into Cortex and may be misleading after the sandboxd boundary cleanup; P711 should patch it if still active.
- `docs/architecture/service-topology.md:29` says `Agent scope/context/work trace/payload manifest/sandbox`; P711 should inspect whether this should say shell orchestration instead of sandbox ownership.
- `docs/architecture/overview.md` and `docs/architecture/data-ownership.md` should be checked for whether `sandbox` wording means orchestration or execution ownership.
