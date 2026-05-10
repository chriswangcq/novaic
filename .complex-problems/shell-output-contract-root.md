# Shell output contract normalization

## Problem

Runtime has a `ToolOutputV1` envelope, but the `shell` executor still returns the raw Cortex shell dict and relies on generic legacy wrapping. That means the LLM-facing text is a serialized implementation dict instead of a deliberate shell summary, and full stdout/stderr preservation is not explicitly separated from bounded prompt text.

This weakens the file/display/shell architecture: shell should be a clean command substrate, while the model should receive bounded text plus durable diagnostics/artifact metadata.

## Success Criteria

- `shell` tool results are explicitly normalized into `ToolOutputV1` by the shell executor path, not by legacy wrapping.
- LLM-facing `text` includes a concise bounded shell summary with exit code and stdout/stderr previews.
- Full raw shell result is preserved in diagnostics for payload-level recovery, while prompt-facing text stays bounded.
- Nonzero shell exit codes map to `ok=false` and `tool_status=error`.
- Tests cover success, nonzero exit, and large output truncation.
