# Fix cross-package pytest tests namespace conflict

## Problem

Focused tests from multiple subprojects cannot reliably run in one pytest process because multiple packages expose a top-level `tests` package. In particular, Cortex tests import helpers via `from tests...`, which resolves to the wrong package when `novaic-agent-runtime` appears first on `PYTHONPATH`. This makes schema/policy verification order-dependent and violates the explicit dependency boundary expected for the audit.

## Success Criteria

- Cortex schema tests no longer depend on a generic top-level `tests` package for helper imports.
- A combined focused pytest command covering runtime tool surface policy and Cortex tool schema limits passes in one process.
- The cleanup removes or neutralizes the stale `tests` package ambiguity instead of adding a brittle local fallback.
