# Shell LLM Output Is Terminal Preview Only

## Problem

Tighten the runtime shell output contract so the LLM-facing `tool-output.v1` text behaves like a terminal preview: exit code, bounded stdout/stderr, truncation markers, and small metadata. It must not duplicate full raw stdout/stderr in diagnostics. Full replay remains available from Cortex step/payload storage.

## Success Criteria

- `raw_shell_result` is removed from shell `tool-output.v1.diagnostics`.
- Shell diagnostics keep only small, explicit fields such as exit code, stdout/stderr char counts, truncation flags, and changed file count.
- Shell text remains useful and bounded for success and nonzero exit cases.
- Unit tests cover large stdout/stderr and assert full raw output is not embedded in the LLM-facing envelope.
