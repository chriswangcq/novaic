# Normalize shell results into ToolOutputV1

## Problem Definition

The shell executor returns a raw dict from Cortex and lets `_ok()` convert it through the generic legacy path. This keeps compatibility, but it fails the newer contract goal: shell output should have a deliberate prompt projection and preserve raw recoverable data separately.

## Proposed Solution

Implement a shell-specific output builder in Runtime:

- Convert Cortex shell result dicts into `ToolOutputV1` directly.
- Produce bounded text containing exit code, stdout preview, stderr preview, and changed files.
- Store the raw shell result in diagnostics under an explicit key for payload-level recovery.
- Treat nonzero exit codes as `ok=false`, preserving stderr/error summary.

## Acceptance Criteria

- `_exec_shell` returns a `tool-output.v1` dict.
- Successful shell output is concise and includes stdout preview.
- Nonzero shell output sets `ok=false` and Runtime marks `tool_status=error`.
- Long stdout is truncated in `text` and marked in diagnostics.
- Existing generic legacy wrapping remains only for non-shell executors.

## Verification Plan

- Add/extend unit tests for shell output normalization.
- Run shell output tests plus existing tool handler contract tests.

## Risks

- Changing nonzero shell exit behavior from generic success to logical error may affect old prompts, but it is the correct contract for command execution.
- Raw diagnostics can be large; prompt projection must continue to ignore diagnostics except through explicit payload inspection.

## Assumptions

- Raw diagnostics live in the durable tool payload and are not injected wholesale into LLM context by Cortex projection.
