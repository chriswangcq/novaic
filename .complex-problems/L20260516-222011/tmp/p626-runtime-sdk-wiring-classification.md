# P626 Runtime Shell Handler SDK Wiring Classification

## Active Path

Runtime shell execution is a two-hop service boundary:

1. `task_queue.handlers.tool_handlers._exec_shell` constructs explicit capability env and calls `bridge.shell_exec(command, timeout, capability_env=...)`.
2. `task_queue.utils.cortex_bridge.CortexBridge.shell_exec` POSTs to Cortex `/v1/internal/shell` with tenant fields, command, timeout, and env.
3. Cortex owns the sandbox SDK/sandboxd dependency (`novaic_cortex.sandbox`, covered by sibling/parent checks), so runtime does not import `sandbox_sdk` directly.

This is acceptable for P626: runtime does not execute locally; it delegates to Cortex's internal shell service boundary, which is backed by sandboxd.

## Intended Hits

- `tool_handlers.py` shell handler calls `bridge.shell_exec`, not subprocess.
- `cortex_bridge.py` posts `/v1/internal/shell` and converts transport failures into a shell-like error result.
- Tests assert explicit capability env propagation and `/v1/internal/shell` path.

## Risky-Looking Hits

- `main_novaic.py` uses `subprocess.Popen` to supervise backend worker/service processes. That is runtime process orchestration, not user shell execution, and is covered by P627 residue classification.
- `runtime_roster.py` and tests mention subprocess as service supervision/test fixture, not active shell execution.

## Verification

- Focused tests passed: 7 tests in shell output contract plus CortexBridge shell env path test.

## Conclusion

No active runtime shell-handler bypass of Cortex/sandboxd was found in P626 scope.
