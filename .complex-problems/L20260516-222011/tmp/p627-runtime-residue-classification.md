# P627 Runtime Legacy Execution Residue Classification

## Intended Production Hits

- `main_novaic.py::run_vmcontrol` imports and uses `subprocess.Popen` to supervise the Rust `vmcontrol` service process. This is backend process orchestration, not agent shell execution.
- `task_queue/workers/runtime_roster.py` contains canonical launch command strings and process check patterns for runtime worker supervision. This is worker roster SSOT, not shell execution.
- `task_queue/utils/cortex_bridge.py::shell_exec` posts to `/v1/internal/shell`; this is the active user shell execution boundary.
- `task_queue/handlers/tool_handlers.py::_exec_shell` calls `bridge.shell_exec` and returns bounded tool-output contract text.

## Test/Fixture Hits

- `tests/test_pr343_runtime_worker_roster_ssot.py` uses `subprocess.check_output` to test the roster CLI. This is a test harness use.
- Legacy/compat/fallback words in tests such as `test_pr255_legacy_compat_cleanup.py` and `test_pr315_queue_fsm_final_residue_guard.py` are guardrail assertions that old paths remain removed.
- Many `host` hits are CLI bind-host arguments or service URL fixtures.

## Risky Active Runtime Bypass

None found. No active runtime tool handler path executes user commands with local subprocess or host mounts. User shell goes through `_exec_shell -> CortexBridge.shell_exec -> /v1/internal/shell`.

## Hygiene Finding

Generated `__pycache__` files exist in the working tree (`410` files under `novaic-agent-runtime` during this scan) but none are tracked. This is workspace hygiene, not a runtime code path. Clean before final status/commit if committing.

## Verification

- Runtime worker roster/legacy/FSM/shell-output focused suite passed after running from the correct `novaic-agent-runtime` cwd: 17 tests.
- Runtime tool path contract tests passed: 9 tests.
