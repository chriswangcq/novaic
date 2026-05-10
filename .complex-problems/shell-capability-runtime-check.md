# Shell capability runtime substrate success check

## Result IDs

- R000

## Evidence

- `novaic-cortex/novaic_cortex/sandbox.py` generates `agentctl`, `runtimectl`, and `cortex` command wrappers inside each disposable sandbox and prepends the generated bin directory to `PATH`.
- `novaic-cortex/tests/test_shell_capability_runtime.py` verifies command presence, help output, stable path sanitization, and no RO materialization for help/presence checks.
- `python -m pytest tests/test_shell_capability_runtime.py tests/test_sandbox_sync.py -q` passed with `5 passed, 1 skipped`.

## Criteria Map

- Fresh sandbox executions have stable commands on `PATH`: satisfied by `command -v agentctl runtimectl cortex`.
- Help commands work: satisfied by `agentctl --help`, `runtimectl --help`, and `cortex payload --help`.
- Commands are generated inside each disposable sandbox and read config from stable env/config: satisfied by generated wrapper scripts and `.novaic_env.json`/environment loader.
- Tests prove presence and lazy RO behavior: satisfied by the new test file.

## Execution Map

- Implemented the substrate directly in Cortex sandbox creation.
- Verified with focused tests and adjacent stable-path/lazy-RO tests.

## Stress Test

- The tests seed RO data and then assert no `/ro/` prefixes or keys are listed/read for command presence/help commands, proving help usage does not pull historical Cortex state.

## Residual Risk

- Rich runtime/cortex operations still need to be added as separate tickets behind the now-stable command substrate.
