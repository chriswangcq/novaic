# Rerun hidden input focused tests from correct runtime cwd

## Problem

The P474 focused pytest command failed because relative-path guard tests were run from the repo root instead of `novaic-agent-runtime`. Rerun the same focused suite from the correct cwd and preserve guard artifacts.

## Success Criteria

- Run the focused pytest suite from `novaic-agent-runtime` or otherwise make relative-path tests resolve correctly.
- Save rerun logs under `.complex-problems/L20260516-222011/tmp/p478/`.
- Confirm hidden-input guards still pass.
- Record whether the verification now passes or exposes a real code/test issue.
