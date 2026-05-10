# Legacy DFS renderer deletion check

## Result IDs

- R060

## Criteria Map

- Delete or remove active-package exports for `ContextEngine`, `StepTree`, and `prepare_messages_for_llm`: satisfied.
- Delete `engine.py` and `step_tree.py` if no current non-test runtime depends on them: satisfied.
- Delete or migrate direct `ContextEngine` tests to event projection/read-model tests: satisfied.
- Keep only intentional source-guard strings, with no production imports or reachable fallback: satisfied.
- Static scans show no production `ContextEngine`, `StepTree`, or `prepare_messages_for_llm` residue: satisfied.
- Full Cortex test suite passes: satisfied.

## Execution Map

- `context_stack/__init__.py` now exports only shared budget/status types.
- The old renderer files were deleted.
- Direct DFS tests were deleted.
- PR-84 invariant coverage was moved to event-written API context plus `context_prepare_for_llm`.
- PR-67 default status guard now monkeypatches `ContextEventReadModel.prepare` to prove default status does not render LLM context.
- Event projection now handles wake-close summary folding and system-prompt ordering explicitly.

## Evidence

Production scan:

```bash
rg -n "ContextEngine|StepTree|prepare_messages_for_llm|context_stack\\.engine|context_stack\\.step_tree" novaic-cortex/novaic_cortex
```

Result: no matches.

Remaining package files:

```text
novaic-cortex/novaic_cortex/context_stack/__init__.py
novaic-cortex/novaic_cortex/context_stack/budget.py
novaic-cortex/novaic_cortex/context_stack/types.py
```

Focused tests: `41 passed`.

Full Cortex tests: `430 passed`.

## Stress Test

The check deliberately treats bypassed legacy code as a failure. After the cleanup, production symbol scans cannot find the old renderer API at all, so future code cannot accidentally import the old DFS path without reintroducing it explicitly.

## Residual Risk

Only source-guard test strings mention the old symbols. This is intentional and does not preserve runtime code. The old direct DFS tests are gone, so behavior is now covered by event projection/read-model/API tests.

## Verdict

Successful.
