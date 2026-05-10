# Shell capability runtime substrate implemented

## Summary

Implemented a minimal generic shell capability substrate in Cortex sandbox. Every disposable sandbox execution now creates a private command directory and prepends it to `PATH`, exposing `agentctl`, `runtimectl`, and `cortex` without relying on host-installed entry points.

## Done

- Added sandbox-generated command wrappers in `novaic-cortex/novaic_cortex/sandbox.py`.
- Added stable command help behavior for:
  - `agentctl --help`
  - `runtimectl --help`
  - `cortex payload --help`
- Kept the implementation self-contained inside generated scripts, so commands do not import from the repo while running from sandbox RW.
- Ensured shell output sanitization maps wrapper paths to stable `/cortex/bin/...`.
- Added `novaic-cortex/tests/test_shell_capability_runtime.py`.

## Verification

- Ran `python -m pytest tests/test_shell_capability_runtime.py tests/test_sandbox_sync.py -q` in `novaic-cortex`.
- Result: `5 passed, 1 skipped`.

## Residual Risk

- The substrate currently exposes reliable help and command wiring only. Rich `agentctl`/`runtimectl` behavior still needs follow-up implementation behind this substrate.
- The current generated script includes an HTTP request helper for future commands, but help paths do not use it.
