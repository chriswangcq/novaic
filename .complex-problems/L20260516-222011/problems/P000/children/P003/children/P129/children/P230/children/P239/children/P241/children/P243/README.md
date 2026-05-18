# Migrate Cortex helpers to package-specific test namespace

## Problem

Cortex shared test helpers need a package-specific namespace so Cortex tests do not import through generic `tests.*`. This belongs under the namespace cleanup ticket because it is the actual code change that removes order-dependent import behavior.

## Success Criteria

- Cortex helper modules used by tests live under a Cortex-specific helper package or equivalent unambiguous namespace.
- Cortex test files import the unambiguous namespace instead of `tests.*`.
- `novaic-cortex/tests/__init__.py` is removed or proven unnecessary and deleted.
- No compatibility shim preserves the old generic `tests.*` path.
