# Repair submodule dirty-state capture

## Problem

Redo the per-submodule dirty-state capture with a robust command that does not trigger shell `printf` option parsing errors. Record corrected evidence for submodule branch/status boundaries.

## Success Criteria

- Per-submodule output includes clear headers or path labels.
- Each submodule branch and `git status --short` output is captured or explicitly bounded.
- The command exits without the previous `printf: --: invalid option` errors.
- The result supersedes the weak dirty-state claim in R001.
