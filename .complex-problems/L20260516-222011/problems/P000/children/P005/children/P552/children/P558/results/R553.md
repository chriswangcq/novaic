# P558 Result: LogicalFS Sandbox Blob Entry Points And Tests Map

## Summary

Completed a bounded read-only map of the active LogicalFS / sandbox / blob entrypoints and the focused tests that cover them. The map confirms the current intended direction: Cortex owns Workspace semantics, LogicalFS provides generic materialization/diff, sandboxd owns process execution, Blob Service owns cheap byte/object storage, and agent-runtime owns shell/display tool-output projection into LLM history.

## Done

- Generated an entrypoint inventory with 256 files:
  - `.complex-problems/L20260516-222011/tmp/p558/entrypoint-files.txt`
- Generated a related test inventory with 87 files:
  - `.complex-problems/L20260516-222011/tmp/p558/test-files.txt`
- Captured line-numbered code slices for the main boundaries:
  - `.complex-problems/L20260516-222011/tmp/p558/entrypoint-slices.txt`
- Wrote a human map tying code entrypoints to test coverage:
  - `.complex-problems/L20260516-222011/tmp/p558/test-map.md`
- Mapped the critical runtime chain:
  - `main_cortex.py` wires `SandboxdClient`.
  - `api.py` exposes `/v1/shell`.
  - `runtime.py` delegates shell to `Sandbox.exec`.
  - `sandbox.py` acquires LogicalFS, executes through sandboxd, releases RW patches.
  - `logical_fs.py` projects bounded `/cortex/ro` and `/cortex/rw`.
  - `sandbox_service/main.py` owns `/v1/execute`.
  - `blob_service/routes.py` owns blob/object APIs.
  - `tool_handlers.py`, `step_result_projection.py`, and `utils/context.py` own shell/display LLM projection.

## Verification

- Verified by file inventory counts:
  - `entrypoint-files.txt`: 256 lines.
  - `test-files.txt`: 87 lines.
  - `entrypoint-slices.txt`: 1750 lines.
- Verified the key entrypoint slices include line-numbered evidence for:
  - Cortex service wiring.
  - Shell execution path through sandboxd.
  - LogicalFS materialization and release.
  - Sandbox service `/v1/execute`.
  - Blob Service blob/object routes.
  - Runtime shell/display tool-output projection.
- This ticket was read-only by design; no production code or tests were modified.

## Known Gaps

- This ticket maps entrypoints and tests only; it does not classify or remediate residue.
- P553 must classify two already-visible risk items:
  - `Workspace.materialize()` naming/API shape.
  - `logicalfs.BlobObjectStore` as a below-LogicalFS adapter that must not become a workspace authority bypass.
- P555 must run focused tests after residue/remediation work completes.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p558/entrypoint-files.txt`
- `.complex-problems/L20260516-222011/tmp/p558/test-files.txt`
- `.complex-problems/L20260516-222011/tmp/p558/entrypoint-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p558/test-map.md`
