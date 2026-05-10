# Current RO/RW Mount Path Audit Result

## Summary

Current shell execution uses a disposable temp sandbox per command. Runtime sends shell commands to Cortex with capability env; Cortex creates a new temp `ro`, `rw`, and `bin`; optionally materializes RO; always materializes RW; rewrites stable `/cortex/*` paths to temp paths; runs the process; scans RW before/after; persists changed RW files back to CortexStore. The design is clean and reliable, but repeated list/get/copy work is the core latency source.

## Done

- Traced Runtime shell tool path:
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:174-205` builds capability env and calls `bridge.shell_exec`.
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:318-339` posts `/v1/internal/shell`.
  - `novaic-cortex/novaic_cortex/api.py:1870-1882` receives the request and calls `Cortex.tool_shell`.
  - `novaic-cortex/novaic_cortex/runtime.py:199-214` delegates to `sandbox.exec`.
- Traced sandbox mount path:
  - `novaic-cortex/novaic_cortex/sandbox.py:978-986` uses a regex heuristic to decide if RO is needed.
  - `novaic-cortex/novaic_cortex/sandbox.py:1015-1017` documents the sandbox as disposable.
  - `novaic-cortex/novaic_cortex/sandbox.py:1033-1039` maps store prefixes to full agent-level `/ro/` and `/rw/`.
  - `novaic-cortex/novaic_cortex/sandbox.py:1057-1093` lists each requested prefix and downloads every object under that prefix into temp directories.
  - `novaic-cortex/novaic_cortex/sandbox.py:1135-1144` creates new temp dirs and materializes workspace on every exec.
  - `novaic-cortex/novaic_cortex/sandbox.py:1164-1181` injects stable env and `.novaic_env.json`.
  - `novaic-cortex/novaic_cortex/sandbox.py:1183-1189` snapshots RW and rewrites stable paths.
  - `novaic-cortex/novaic_cortex/sandbox.py:1231-1233` scans RW after exec and persists changed files.
- Traced persistence and store cost:
  - `novaic-cortex/novaic_cortex/sandbox.py:916-939` recursively scans RW for before/after stats.
  - `novaic-cortex/novaic_cortex/sandbox.py:1095-1111` deletes removed files and writes changed files.
  - `novaic-cortex/novaic_cortex/blob_store.py:91-109` implements recursive list as one Blob Service list call, then each object download is a separate GET.
- Identified current mitigations:
  - RO is lazy unless command text references `$RO`, `$CORTEX_RO`, `$CORTEX_ROOT`, `/cortex`, or `/cortex/ro`.
  - Materialization is concurrent with `_MATERIALIZE_CONCURRENCY = 16`.
  - `max_sync_bytes` can stop oversized syncs before execution.
  - Temp backing paths are sanitized from output.
- Identified confirmed bottlenecks:
  - Every command creates a fresh temp filesystem and capability script directory.
  - Every command always materializes full RW, even for `echo`, `agentctl`, or commands that do not read/write workspace files.
  - Any command touching RO materializes the entire agent-level RO prefix, not only the referenced files or current subagent root.
  - RO/RW materialization cost grows with historical scopes, payloads, config, skills, and user scratch files.
  - RW persistence requires full recursive stat before and after execution.
  - Blob-backed production pays list plus N object GETs per mounted prefix per command.

## Verification

- Used focused code inspection with `rg` and `nl`.
- Cross-checked behavior against tests:
  - `novaic-cortex/tests/test_incremental_sync.py:12-32` locks disposable no-cross-exec state.
  - `novaic-cortex/tests/test_incremental_sync.py:45-59` locks RW persistence across execs through store, not cache.
  - `novaic-cortex/tests/test_sandbox_stress.py:20-64` locks timeout clamping behavior.

## Known Gaps

- none for this audit subproblem.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/runtime.py`
- `novaic-cortex/novaic_cortex/sandbox.py`
- `novaic-cortex/novaic_cortex/blob_store.py`
- `novaic-cortex/tests/test_incremental_sync.py`
- `novaic-cortex/tests/test_sandbox_stress.py`
