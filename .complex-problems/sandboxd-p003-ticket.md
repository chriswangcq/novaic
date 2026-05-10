# Wire Cortex active server path to sandboxd

## Problem Definition

Cortex still constructs `Sandbox` with an in-process runner and pre-wraps commands through LogicalFS. The production HTTP server path must explicitly use the sandboxd client and pass declarative mount plans, while unit tests may inject a direct runner.

## Proposed Solution

Make the sandbox process runner an explicit dependency. Add a Cortex API runner factory configured by `main_cortex --sandboxd-url`, update `Sandbox`/`ShellExecutionOrchestrator` to pass `ProcessSpec.mount`, and add tests proving the server helper injects the runner and Cortex no longer pre-wraps commands before calling the runner.

## Acceptance Criteria

- `Sandbox` and `Cortex` accept explicit process-runner dependencies.
- `main_cortex` requires/configures `--sandboxd-url` and installs a `SandboxdProcessRunner` factory.
- API-created Cortex instances use the configured runner.
- LogicalFS exposes a mount plan; Cortex no longer calls `build_bind_mount_command` directly in the orchestrator path.
- Tests verify injected runner usage and command/mount separation.

## Verification Plan

- Run focused Cortex sandbox/API tests.
- Run source scans for active command pre-wrapping in `sandbox.py`.

## Risks

- Existing unit tests instantiate `Cortex` directly and should continue to use the explicit local test adapter by default.

## Assumptions

- Production entrypoint wiring, not raw library construction, defines the active server path.
