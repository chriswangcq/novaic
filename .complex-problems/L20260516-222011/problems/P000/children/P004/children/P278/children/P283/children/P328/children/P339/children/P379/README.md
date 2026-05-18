# Cortex archive diagnostics aggregate regression

## Problem

Cortex scope-end and context-event lifecycle behavior needs a focused regression pass to prove archive diagnostics use explicit request payloads rather than implicit active state, preserve context projection semantics, and reject unsafe generation coercion.

## Success Criteria

- Focused Cortex lifecycle, scope archive, projection, model, and write-authority tests pass.
- Source guards prove archive diagnostics do not look up current active generation or synthesize remaining stack from hidden state.
- Bool or missing `session_generation` diagnostics behavior is verified as fail-closed where diagnostics are present.
- Any unsafe Cortex hit is fixed or converted into a follow-up problem.
