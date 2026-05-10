# Remove legacy DFS renderer residue

## Problem Definition

The Cortex LLM context API now uses event projection, but the legacy DFS renderer remains physically present in the active package and several tests still preserve direct `ContextEngine` semantics. This violates the user's full-cut/no-old-logic requirement.

## Proposed Solution

Perform a bounded physical cleanup:

- Inspect all remaining `ContextEngine`, `StepTree`, and `prepare_messages_for_llm` references.
- Delete `context_stack/engine.py` and `context_stack/step_tree.py` if runtime scans prove they are not needed.
- Remove `ContextEngine` and `StepTree` exports from `context_stack/__init__.py`.
- Delete or migrate direct DFS renderer tests.
- Update default-status tests to assert they do not call the event read model, rather than monkeypatching the old renderer.
- Keep source-guard tests only as intentional scan strings.

## Acceptance Criteria

- No production import/export/reference to `ContextEngine`, `StepTree`, or `prepare_messages_for_llm`.
- Direct `ContextEngine` tests are deleted or migrated.
- Event read model and projection tests cover the intended behavior.
- Static scans distinguish intentional guard strings from real runtime residue.
- Full Cortex tests pass.

## Verification Plan

- Run targeted `rg` scans for old renderer symbols.
- Run focused tests around context event projection, read model, source guards, status API, and minimal structure invariants.
- Run the full Cortex test suite.

## Risks

- Some tests may still encode valid behavior that needs to be moved to event projection tests before deletion.
- Removing exports may expose hidden runtime imports outside the current test set.
- The cleanup could require small API/test rewrites rather than pure deletion.

## Assumptions

- Active LLM context reading is already event-projected and should remain so.
- Legacy DFS renderer is not required as a compatibility path.
- The user's stated preference allows deleting old tests and old data/compat code.
