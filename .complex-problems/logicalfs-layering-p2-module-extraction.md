# Extract module boundaries for shell capabilities, LogicalFS, and process execution

## Problem

`novaic_cortex/sandbox.py` currently owns unrelated concerns. This makes the layering hard to reason about and increases the risk of future changes landing in the wrong layer.

## Success Criteria

- Capability CLI generation is moved to a shell-facing module.
- LogicalFS materialization, mount namespace wrapping, and stable path sanitization are moved to a LogicalFS module.
- Process execution dataclasses/runner are moved to an execution module.
- `sandbox.py` remains the thin public facade/orchestrator.
- Public behavior stays unchanged.
