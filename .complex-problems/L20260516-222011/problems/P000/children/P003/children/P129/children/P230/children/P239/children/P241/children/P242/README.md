# Inventory Cortex test helper imports and package markers

## Problem

Before modifying imports, identify every Cortex test dependency on generic `tests.*` imports and the package marker files that create top-level `tests` package ambiguity. This belongs under the namespace cleanup ticket because the implementation should be based on an explicit import inventory rather than a blind replace.

## Success Criteria

- Produce an evidence-backed list of Cortex `tests.*` imports that must change.
- Identify whether `novaic-cortex/tests/__init__.py` has any active purpose beyond making a top-level package.
- Record any non-Cortex `tests.*` dependency that could still affect the combined focused verification command.
