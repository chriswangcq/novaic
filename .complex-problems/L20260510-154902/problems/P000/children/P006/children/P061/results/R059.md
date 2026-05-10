# Phase 5 final verification result

## Summary

Phase 5 final verification ran the source-of-truth scans and the full Cortex test suite. The active LLM context read path is event-projected, and the full Cortex tests pass, but the final strict diff review found physical legacy DFS renderer residue that still violates the user's full-cut/no-old-logic standard.

## Done

- Verified `prepare_for_llm` source no longer calls `ContextEngine`, `prepare_messages_for_llm`, `read_context`, `StepTree`, or `_collect_active_stack`; it uses `ContextEventReadModel`.
- Verified `/v1/context/status` with usage accounting uses `ContextEventReadModel`; the only remaining `_collect_active_stack` usage is the cheap non-usage operational status path.
- Ran the full Cortex suite with event-projection changes: `455 passed`.
- Scanned remaining `ContextEngine`, `StepTree`, and `prepare_messages_for_llm` references.

## Evidence

Active source scan:

```text
[prepare]
ContextEngine: False
prepare_messages_for_llm: False
read_context: False
StepTree: False
_collect_active_stack: False
ContextEventReadModel: True

[status]
ContextEngine: False
prepare_messages_for_llm: False
read_context: False
StepTree: False
_collect_active_stack: True
ContextEventReadModel: True
```

Full test command:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests
```

Result:

```text
455 passed
```

Residual legacy scan still found production/test files containing the old DFS renderer symbols:

```text
novaic-cortex/novaic_cortex/context_stack/__init__.py
novaic-cortex/novaic_cortex/context_stack/engine.py
novaic-cortex/novaic_cortex/context_stack/step_tree.py
novaic-cortex/tests/test_context_event_read_source_guards.py
novaic-cortex/tests/test_pr66_system_scope_rendering.py
novaic-cortex/tests/test_pr67_wake_child_api.py
novaic-cortex/tests/test_pr73_folded_scope_rendering.py
novaic-cortex/tests/test_pr84_minimal_structure_invariants.py
```

## Gaps

- The active API path is cut over, but `context_stack/engine.py` and `context_stack/step_tree.py` still physically exist.
- Several tests still reference or preserve direct `ContextEngine` semantics, even if the active path no longer uses it.
- Under the user's explicit standard, this is not acceptable as final completion: old logic must be deleted or migrated, not merely bypassed.

## Next Required Follow-Up

Create and solve a physical legacy DFS deletion/migration follow-up:

- Delete or isolate old DFS renderer code from the active package.
- Remove `ContextEngine` and `StepTree` exports.
- Delete or migrate direct `ContextEngine` tests to event projection/read-model tests.
- Keep only source-guard strings, if any.
- Re-run full Cortex tests.
