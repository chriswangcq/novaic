# P062: Physically delete legacy DFS renderer and direct tests

Status: done
Parent: P061
Root: P000
Package: problems/P000/children/P006/children/P061/children/P062
Body: problems/P000/children/P006/children/P061/children/P062/README.md
Ticket(s): T062

## Problem
Phase 5 proved the active LLM context API reads through the event projection, but legacy DFS renderer code still exists physically in the active package. This violates the full-cut/no-old-logic requirement and creates a future maintenance hazard.

The remaining residue includes:

- `novaic_cortex/context_stack/engine.py`
- `novaic_cortex/context_stack/step_tree.py`
- `context_stack/__init__.py` exports for old renderer types
- Direct `ContextEngine` tests or monkeypatches that preserve the old API surface

## Success Criteria
- Delete or remove active-package exports for `ContextEngine`, `StepTree`, and `prepare_messages_for_llm`.
- Delete `engine.py` and `step_tree.py` if no current non-test runtime depends on them.
- Delete or migrate direct `ContextEngine` tests to event projection/read-model tests.
- Keep only intentional source-guard strings, with no production imports or reachable fallback.
- Static scans show no production `ContextEngine`, `StepTree`, or `prepare_messages_for_llm` residue.
- Full Cortex test suite passes.

## Subproblems
- none

## Results
- R060

## Latest Check
C063

## Bodies
- Problem: problems/P000/children/P006/children/P061/children/P062/README.md
- Ticket T062: problems/P000/children/P006/children/P061/children/P062/tickets/T062.md
- Result R060: problems/P000/children/P006/children/P061/children/P062/results/R060.md
- Check C063: problems/P000/children/P006/children/P061/children/P062/checks/C063.md

## Follow-ups
- none
