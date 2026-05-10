# SubAgent tool schema cutover success check

## Status

success

## Result IDs

- R000

## Criteria Map

- LLM schemas exclude `subagent_spawn`: satisfied by Cortex schema guard tests and Common product semantics tests.
- Shell schema advertises replacement command: satisfied by shell schema tests and shell help tests.
- `agentctl subagent spawn` executes through sandbox capability script: satisfied by `test_agentctl_subagent_spawn_round_trip_through_shell`.
- Runtime guards classify direct executor as compatibility: satisfied by `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS` and Runtime tool-surface tests.

## Execution Map

- `novaic-cortex/novaic_cortex/sandbox.py`: added `agentctl subagent spawn`.
- `novaic-common/common/tools/llm_builtin.py`: removed `subagent_spawn` from active LLM schema and advertised shell command.
- `novaic-common/common/tools/definitions.py`: removed active runtime metadata entry.
- `novaic-agent-runtime/task_queue/tool_surface_policy.py`: classified `subagent_spawn` as completed schema cutover.

## Evidence

- Runtime targeted tests: `31 passed`.
- Cortex targeted tests: `18 passed`.
- Common targeted tests: `11 passed`.

## Stress Test

The shell capability test writes a task file in the disposable sandbox and invokes `agentctl subagent spawn --task-file ... --share-context --timeout-minutes ...`, validating file-oriented ergonomics and the exact Business spawn payload.

## Residual Risk

The direct executor remains for compatibility and final deletion, but it is no longer part of the canonical LLM-visible schema.
