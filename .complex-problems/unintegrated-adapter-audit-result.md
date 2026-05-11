# Unintegrated Adapter Audit Result

## Summary

The audit found two live integration gaps and several cleanup-only residues.

Live gaps:

1. `subagent_wake` can still be created through generic saga creation surfaces, bypassing the session outbox boundary.
2. Shell still materializes the full `/rw/` tree for every command, so large RW workspaces can recreate the same broad-sync class of latency issue that was just fixed for `/ro`.

Cleanup-only residues:

- Cortex Runtime comments/docstrings still say `ContextEngine` / `DFS` even though active context preparation is ContextEvent-backed.
- Historical activity labels/tests still mention old direct tool names, but current schemas and executors no longer expose them.
- Materialized `context.jsonl`/`summary.md` remains for debug/history/projection and archive labels; it is not active LLM context source.

## Done

- Closed `P001` LogicalFS/Sandbox audit with result `R000` and check `C000`.
- Closed `P002` Queue FSM/Saga/session audit with result `R001` and check `C001`.
- Closed `P003` shell capability/tool CLI migration audit with result `R002` and check `C002`.
- Closed `P004` Cortex context event source audit with result `R003` and check `C003`.
- Closed `P005` deployment/compatibility residue audit with result `R004` and check `C004`.

## Verification

- Static code inspection covered:
  - `novaic-cortex/novaic_cortex/logical_fs.py`
  - `novaic-cortex/novaic_cortex/sandbox.py`
  - `novaic-cortex/novaic_cortex/api.py`
  - `novaic-cortex/novaic_cortex/context_event_read_model.py`
  - `novaic-agent-runtime/queue_service/session_repo.py`
  - `novaic-agent-runtime/queue_service/session_outbox.py`
  - `novaic-agent-runtime/task_queue/handlers/saga_handlers.py`
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-agent-runtime/task_queue/tool_surface_policy.py`
  - `novaic-agent-runtime/task_queue/workers/runtime_roster.py`
  - `novaic-common/common/tools/llm_builtin.py`
  - `novaic-business/business/prompt_defaults.py`
  - root `deploy`
  - `scripts/start.sh`
- Targeted tests run for context cutover:

```text
PYTHONPATH=... pytest -q \
  novaic-cortex/tests/test_context_event_no_compat.py \
  novaic-cortex/tests/test_context_event_read_source_guards.py \
  novaic-cortex/tests/test_pr234_control_stack.py

13 passed in 0.34s
```

- Live deployment status checked with `./deploy status`; all core services and runtime roles are healthy.

## Known Gaps

### Gap A: Generic saga creation can bypass session outbox

`queue_service/routes.py` exposes `POST /api/queue/sagas/create`, and `task_queue/handlers/saga_handlers.py` handles `SagaTopics.SAGA_TRIGGER` by calling saga creation for arbitrary saga types. Current app code uses this for legitimate child sagas (`react_think`, `react_actions`, `wake_finalize`), but the surface does not forbid `subagent_wake`. That leaves an old-style wake creation path physically possible outside `SessionRepository.dispatch()` and `SessionOutboxDispatcher`.

Recommended fix:

- Add an explicit saga creation policy.
- Allow `SAGA_TRIGGER` only for child/internal saga types that are not session-owned.
- Require `subagent_wake` creation to enter only through the durable session outbox dispatcher.
- Add tests that direct `/sagas/create` or `saga.trigger` cannot create `subagent_wake`.

### Gap B: Shell still broad-syncs `/rw/`

`MountNamespaceLogicalFS._workspace_snapshot()` still calls `_add_tree(files, "/rw/")`, which reads the full writable tree through `Workspace.read_tree_bytes()`. The `/ro` broad-sync issue is fixed, but this is the same adapter shape on the writable side.

Recommended fix:

- Scope RW materialization to the current subagent work directory plus explicit shared/public directories.
- Keep `.novaic_env.json` injected.
- Avoid full recursive `/rw/` copy on every command.
- Add a regression test proving unrelated/big RW trees are not materialized for simple shell commands.

### Gap C: Comment/docstring residue around old ContextEngine/DFS

Active LLM preparation is ContextEvent-backed, but `cortex_handlers.py` and `cortex_bridge.py` still contain stale `ContextEngine`/`DFS` wording. This is not a live path, but it violates the "residue misleads future work" principle.

Recommended fix:

- Rewrite stale comments/docstrings to say ContextEvent read model, active-stack projection, and materialized debug projection accurately.

### Gap D: Historical direct-tool names remain in projection/test fixtures

Current LLM schemas and `_EXECUTORS` expose only `shell`, `display`, `skill_begin`, `skill_end`, `sleep`. Old direct names remain in activity projection labels and old-record tests. This is not live tool exposure, but future cleanup could rename them as historical labels.

Recommended fix:

- Keep runtime boundary tests as hard guards.
- Optionally rename projection labels/comments to `historical_direct_tool_labels` to avoid confusing them with active tools.

## Artifacts

- `.complex-problems/unintegrated-adapter-result-logicalfs.md`
- `.complex-problems/unintegrated-adapter-result-runtime.md`
- `.complex-problems/unintegrated-adapter-result-tools.md`
- `.complex-problems/unintegrated-adapter-result-context.md`
- `.complex-problems/unintegrated-adapter-result-deploy.md`
