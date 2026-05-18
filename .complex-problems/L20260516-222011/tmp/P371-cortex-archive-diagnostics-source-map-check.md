# Cortex Archive Diagnostics Source Map Check

## Summary

Success. The source map identifies the active runtime-to-Cortex archive path, current field handling, relevant tests, and concrete implementation targets for the remaining children.

## Evidence

- R353 lists the active functions/files from wake-finalize payload building through Cortex archive persistence.
- R353 explicitly identifies dropped fields at `handle_cortex_scope_end` and `CortexBridge.scope_end`.
- R353 identifies Cortex persistence as generic `scope_end_root` / `scope_end_child` plus active-stack-derived remaining stack and active-stack-generated generation.
- R353 names runtime and Cortex tests to update.

## Criteria Map

- Active function/file list: satisfied by R353 `Done` and `Current Field Handling`.
- Handling of `session_generation`, `finalize_reason`, and remaining stack: satisfied by R353 `Current Field Handling`.
- Existing tests: satisfied by R353 `Verification`.
- Implementation targets: satisfied by R353 `Implementation Targets`.

## Execution Map

- T360 performed read-only source inspection and recorded R353.
- No production or test code was changed by this source-map child.

## Stress Test

- Source search included both runtime and Cortex packages and covered direct archive keywords plus finalize diagnostics keywords, reducing the chance that only the first visible path was mapped.

## Residual Risk

- Non-blocking for P371: actual propagation and persistence fixes remain under P372 and P373, with aggregate verification under P374.

## Result IDs

- R353
