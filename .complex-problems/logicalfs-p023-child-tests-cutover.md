# Migrate Cortex Tests And Prove Shell Cutover

## Problem

Many tests still instantiate `Workspace(MemoryStore(), ...)` or `Cortex(MemoryStore(), ...)`. Even after code refactor, tests can preserve compatibility paths or miss active shell behavior. This belongs under P023 because successful cutover must be verified through the same behavior surfaces the runtime uses.

## Success Criteria

- Cortex tests are migrated to explicit LogicalFS-backed helpers.
- Targeted tests for Workspace, runtime, API sandbox wiring, and shell RW patch persistence pass.
- Full Cortex test suite passes.
- Residue scans show no direct `Workspace(MemoryStore`, `Cortex(MemoryStore`, `Cortex(store`, or old authority imports in tests except clearly isolated object-store unit tests.
