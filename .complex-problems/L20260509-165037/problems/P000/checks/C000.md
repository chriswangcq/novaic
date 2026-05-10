# Shell capability environment transport success check

## Result IDs

- R000

## Evidence

- Runtime now sends explicit `capability_env` through `CortexBridge.shell_exec()`.
- Cortex API accepts the env mapping on `/v1/internal/shell`.
- Sandbox exposes only allowlisted keys to shell commands.
- Tests passed in both Runtime and Cortex.

## Criteria Map

- Runtime sends explicit env: satisfied by `_exec_shell()` and `CortexBridge.shell_exec(..., capability_env=...)`.
- Cortex forwards only allowlisted env: satisfied by `Sandbox._capability_env()`.
- Commands can inspect context: satisfied by sandbox test reading `NOVAIC_BUSINESS_URL` and `NOVAIC_SCOPE_ID`.
- Existing shell behavior remains compatible: satisfied by adjacent sandbox sync tests.
- Tests prove transport: satisfied by focused Runtime and Cortex tests.

## Execution Map

- Added env field to internal shell request path.
- Threaded env through Cortex runtime and sandbox execution.
- Verified bridge payload and sandbox filtering.

## Stress Test

- Sandbox test passes a disallowed `NOT_ALLOWED` variable and verifies it is not visible in the shell process.

## Residual Risk

- Next tickets must implement actual commands (`agentctl im ...`) using this transported context.
