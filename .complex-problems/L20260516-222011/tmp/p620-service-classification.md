# P620 Sandbox Service Boundary Classification

## Intended Service Boundary

- `sandbox_service/core/process.py` is the sandboxd-internal process runner. It is allowed to call `asyncio.create_subprocess_shell` because sandboxd is the execution service.
- `sandbox_service/core/mount_namespace.py` builds private bind-mount commands with quoted source/mount/cwd arguments; tests cover quoting.
- `sandbox_service/main.py` validates mount source existence and absolute mount/stable cwd before converting SDK requests to core specs.

## Test / Mock Uses

- Host path and mount strings in `tests/` are fixtures for validation and quoting behavior.

## Risky Residue

- No active service bypass/fallback route found inside `novaic-sandbox-service`.
