# Cortex archive diagnostics source guard classification

## Problem

Cortex source must be scanned for archive diagnostics residue: generation coercion, hidden active-state lookup, top-level versus nested remaining-stack confusion, and projection consuming diagnostic stack as semantic stack.

## Success Criteria

- Source guards are run over Cortex lifecycle/projection/writer files and relevant tests.
- Every guard hit is classified as safe, fixed, or moved to a follow-up problem.
- No live Cortex archive diagnostic path synthesizes diagnostics from hidden active state or coerces bool generation.
- Projection semantics remain explicit: top-level `remaining_stack` is semantic; nested `archive_diagnostics.remaining_stack` is diagnostic only.
