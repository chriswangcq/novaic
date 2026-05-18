# Runtime and Tool RW Fixture Rewrite

## Problem

Runtime, metrics, hooks, chaos, and wave tests use `/rw/scratch` as generic writable fixtures. These should use current paths that match whether the file must be shell-visible or only Cortex-readable.

## Success Criteria

- Updates `test_runtime.py`, `test_cortex_chaos.py`, `test_hooks_limits.py`, `test_tool_metrics.py`, and `test_wave4_metrics.py` root scratch fixtures.
- Uses shell-visible current paths where shell/runtime behavior needs mounted files.
- Runs focused tests for touched files.
