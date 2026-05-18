# P629 Mount Ownership Classification

## SDK Layer

- `SandboxBindMount` and `mount` fields in `novaic-sandbox-sdk` are DTO/wire contract only.
- SDK serializes/deserializes `source_root`, `mount_point`, and `stable_cwd`; it does not create namespaces or execute `mount`.
- SDK tests use `/tmp/root`, `/cortex`, and `/cortex/rw` as fixtures.

## Cortex Layer

- `novaic_cortex.logical_fs` projects Workspace data into LogicalFS, chooses the bounded RO/RW working set, writes capability scripts, and returns a `SandboxBindMount` plan with `source_root=<materialized view>`, `mount_point=/cortex`, and `stable_cwd=/cortex/rw`.
- Cortex explicitly documents that it asks sandboxd to bind-mount the materialized view and does not execute local shell processes.
- Tests assert scoped RO/RW materialization, subagent RW filtering, and patch persistence.

## Sandbox Service Layer

- `sandbox_service.main` validates mount source existence and absolute mount/stable cwd, then converts SDK DTOs to `BindMountPlan`.
- `sandbox_service.core.process` is the service-internal process runner and calls `build_bind_mount_command` only inside sandboxd.
- `sandbox_service.core.mount_namespace` builds quoted `unshare --mount --propagation private` and `mount --bind` command strings; tests assert quoting and mount plan passing.

## Runtime Layer

- Runtime does not own mount planning. Runtime shell handling delegates to Cortex `/v1/internal/shell`, covered by P624/P626.
- Runtime `/ro`/`/rw` strings in tests and hints are logical shell paths, not host mount operations.

## Risky Residue

No client-side or runtime mount bypass found. Mount ownership is layered: SDK DTO -> Cortex LogicalFS plan -> sandboxd service namespace execution.
