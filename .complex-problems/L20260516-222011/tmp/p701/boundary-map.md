# Sandbox and Sandboxd Boundary Map

## Classification

Sandboxd is a foundational process execution service. It owns remote execution, timeout/result capture, process runner internals, and bind/mount mechanics when requested by an upstream caller.

Sandboxd does not own Cortex Workspace semantics, LogicalFS file authority, subagent RW layout, display semantics, Blob persistence rules, or agent/product meaning.

## Entrypoint Evidence

- `novaic-sandbox-service/main_sandbox_service.py`: executable service entrypoint that imports `sandbox_service.main:main`.
- `novaic-sandbox-service/sandbox_service/main.py`: independent FastAPI service exposing `/health`, `/api/health`, and `/v1/execute`; validates SDK wire requests and delegates to `AsyncProcessRunner`.
- `scripts/start.sh`: launches `main_sandbox_service.py` on `$PORT_SANDBOXD` and passes `--sandboxd-url` into Cortex.

## SDK / Service / Core Split

- `novaic-sandbox-sdk`: owns cross-process DTOs and HTTP client only. Its README explicitly says it must not execute processes, create mount namespaces, inspect local host capabilities, or import Cortex/product logic.
- `novaic-sandbox-service/sandbox_service/main.py`: owns HTTP service boundary, request validation, and conversion from SDK contracts to core process specs.
- `novaic-sandbox-service/sandbox_service/core/process.py` and `core/mount_namespace.py`: own internal process execution and mount-command construction.

## Cortex Relationship

- `novaic-cortex/novaic_cortex/sandbox.py` is a shell facade/orchestrator. It acquires a LogicalFS view, asks sandboxd via SDK to execute a process, releases the view, and assembles `ShellResult`.
- Cortex owns workspace/shell semantics around the call; sandboxd owns process execution. This is an explicit dependency boundary, not a fallback local execution path.

## LogicalFS Relationship

- LogicalFS owns the executable filesystem view and stable `/cortex` path semantics.
- Sandboxd may receive a bind mount plan and execute over it, but does not decide what files belong to RO/RW or how RW patches persist.

## Residue Disposition

No safe production or docs patch was required. The high-signal code comments and docs already state the intended split: LogicalFS owns file semantics, sandboxd executes, Cortex orchestrates.

## Verification

- `cd novaic-sandbox-sdk && PYTHONPATH=.:../novaic-common python3 -m pytest -q` passed.
- `cd novaic-sandbox-service && PYTHONPATH=.:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q` passed.
- `python3 -m py_compile` passed for sandbox service, SDK, and Cortex sandbox facade files.
