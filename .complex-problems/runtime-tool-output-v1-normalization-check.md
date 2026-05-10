# Runtime ToolOutputV1 normalization check

## Status

not_success

## Result IDs

- R000

## Evidence

- `_ok()` now stores durable `content` as `ToolOutputV1`.
- Logical failure and mounted-device paths are covered by tests.
- Runtime and Cortex focused tests pass.
- `_err()` still stores raw `{"error": ...}` JSON, so handler exceptions and unknown tools do not yet use the same durable envelope.

## Criteria Map

- `_ok()` returns `content` containing JSON with `version == "tool-output.v1"`: satisfied.
- Successful dict output is readable via the `text` field: satisfied.
- Logical failure output keeps `tool_success=false` and preserves the failure message inside `ToolOutputV1.text`: satisfied.
- Mounted device handler tests validate the new envelope: satisfied.
- Existing Runtime tool handler failure and contract tests pass: satisfied.
- Every durable tool result path is uniformly normalized: not fully satisfied because `_err()` is still legacy.

## Execution Map

- Implemented success-path normalization.
- Preserved repeated scope-mismatch recovery by unwrapping `ToolOutputV1.text` in `logical_tool_error_fingerprint`.
- Verified focused Runtime and Cortex tests.

## Stress Test

- If a handler raises or the LLM calls an unknown tool, the saved `content` still bypasses `ToolOutputV1`; this keeps one legacy island alive.

## Residual Risk

- The failure envelope gap should be closed with a child/follow-up ticket before declaring this normalization phase complete.
