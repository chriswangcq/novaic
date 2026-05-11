# LogicalFS and Sandbox adapter audit result

## Summary

The original broad `/ro` shell miss is fixed on the live shell path, and there is no local process fallback bypassing sandboxd. One similar live-path risk remains: the shell adapter still materializes the entire `/rw/` tree for every shell command, so a large RW workspace can recreate the same “substrate optimized, adapter still broad-syncs” failure pattern on the writable side.

## Done

Inspected the Cortex shell boundary and LogicalFS adapter:

- `novaic-cortex/novaic_cortex/sandbox.py` states and implements an explicit sandboxd boundary. If no `SandboxExecutor` is configured, shell execution returns `exit_code=-2` instead of falling back to local execution.
- `ShellExecutionOrchestrator.exec()` acquires a `MountNamespaceLogicalFS` view, sends a `SandboxExecSpec` with a mount plan to sandboxd, releases the view, then applies RW patch changes back through LogicalFS.
- `novaic-cortex/novaic_cortex/logical_fs.py` now limits shell RO snapshot contents to `/ro/config/engine.json`, `/ro/config/tools/_index.json`, current root metadata/index/context event log, and the current wake scope subtree only when `NOVAIC_WAKE_SCOPE_PATH` is explicitly under the root.
- `tests/test_sandbox_requires_mount_namespace.py` covers “no local fallback” and rejects leaked `novaic-cortex-sandbox-*` backing paths.
- `tests/test_sandboxd_wiring.py::test_sandbox_materializes_scoped_ro_working_set_only` verifies current wake files are visible while old sibling wake and unrelated roots are not.

Confirmed remaining risk:

- `MountNamespaceLogicalFS._workspace_snapshot()` still calls `_add_tree(files, "/rw/")`.
- `_add_tree()` delegates to `Workspace.read_tree_bytes()`, which recursively lists and reads every file under that prefix.
- Therefore shell startup is still proportional to total `/rw/` size. This is less dangerous than full `/ro` history because RW is user/sandbox-owned, but it is the same adapter shape and can become a production latency issue if RW grows.

Non-issues / valid broad reads:

- `novaic-cortex/novaic_cortex/runtime.py` loads `/ro/config/tools/` and `/ro/skills/` for runtime tool schema assembly. That is not the shell mount path; it is LLM/tool definition assembly and remains a valid explicit Cortex runtime read.
- Workspace archive functions moving `/ro/active` to `/ro/scopes` are state projection/archival behavior, not shell materialization.

## Verification

- Source search: `rg -n "read_tree_bytes|/ro/|/rw/|materialize|Sandbox|LocalProcessRunner|fallback|legacy|compat" novaic_cortex tests -S`.
- Code inspection:
  - `novaic-cortex/novaic_cortex/sandbox.py`
  - `novaic-cortex/novaic_cortex/logical_fs.py`
  - `novaic-cortex/novaic_cortex/workspace.py`
- Existing tests from the previous fix:
  - `tests/test_sandboxd_wiring.py`
  - `tests/test_sandbox_requires_mount_namespace.py`

## Known Gaps

- Follow-up recommended: make RW materialization scoped or lazy. Candidate policy: mount `/rw/public`, `/rw/system`, current `RW_SELF`, and generated `.novaic_env.json` by default; require explicit CLI/API reads for broad RW scans.
- The current LogicalFS substrate is still materialize-copy-patch, not a true realtime/lazy filesystem. That is acceptable for now after RO scoping, but it is not the final “LogicalFS proxy all realtime file service” ideal.

## Artifacts

- `novaic-cortex/novaic_cortex/logical_fs.py:164`
- `novaic-cortex/novaic_cortex/logical_fs.py:189`
- `novaic-cortex/novaic_cortex/logical_fs.py:204`
- `novaic-cortex/novaic_cortex/sandbox.py:7`
- `novaic-cortex/novaic_cortex/sandbox.py:80`
- `novaic-cortex/tests/test_sandboxd_wiring.py:96`
