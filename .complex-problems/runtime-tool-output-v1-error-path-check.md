# Runtime ToolOutputV1 error path check

## Status

success

## Result IDs

- R001

## Evidence

- `_err()` now writes `tool-output.v1` content with `ok=false`.
- Unknown-tool and executor-exception tests assert the new envelope shape.
- Focused Runtime and Cortex tests pass.

## Criteria Map

- `_err()` stores `content` as `ToolOutputV1` JSON with `ok=false`: satisfied.
- Unknown-tool and exception paths preserve current task status/error semantics: satisfied by tests and unchanged top-level fields.
- Tests assert the failure-path envelope has `version == "tool-output.v1"` and includes the error text: satisfied.
- Focused Runtime tool handler failure tests pass: satisfied.

## Execution Map

- Failure envelope normalized.
- Unknown-tool and exception coverage added.
- Regression tests run across Runtime and Cortex projection boundaries.

## Stress Test

- A raised executor exception still emits exactly one structured `event=tool_call_failed` log line and returns an error envelope instead of raising.
- An unknown tool still returns `success=false` and a user-debuggable top-level error.

## Residual Risk

- No residual risk for this follow-up. Later phases still need shell capability cutover and direct tool surface deletion.
