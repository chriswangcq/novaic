# Runtime prepare-context handler map

## Problem

Agent runtime decides when Cortex context is prepared and passed to the LLM. This handler chain must be mapped to ensure the live LLM request uses the intended ContextEvent-backed snapshot and not stale local continuity.

## Success Criteria

- `cortex_handlers.py`, `runtime_handlers.py`, `context_handlers.py`, `react_think.py`, and `react_think` contracts are mapped around prepare-context.
- The exact handoff between queue saga steps, Cortex prepare response, and LLM handler input is documented.
- Any remaining local cross-wake continuity path is classified as active-safe, dead, or stale.
- Relevant runtime tests or static checks are run for prepare-context assumptions.
