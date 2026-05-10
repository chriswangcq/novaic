# Phase 3E Active Stack Cutover Verification Check

## Summary

P021 is not fully solved yet. R035 proves live `api.py` runtime authority is clean and all tests/compile checks pass, but it also finds a lower-level unresolved residue: `Workspace.resolve_active_scope_path(...)` remains as stack-related file-walk code without explicit repair/debug isolation or deletion.

## Evidence

- Targeted tests passed: 44 tests.
- Full Cortex suite passed: 462 tests.
- `py_compile` passed for `novaic-cortex/novaic_cortex`.
- `api.py` static audit has no `_collect_active_stack` or `resolve_active_scope_path`.
- `workspace.py` still defines `resolve_active_scope_path(...)` and walks `steps/_index.jsonl` scope entries.

## Criteria Map

- Targeted tests cover nesting, mismatch, finalize/open-child behavior, restart recovery, and status reads: satisfied.
- Static residue search proves runtime active-stack authority no longer depends on `_collect_active_stack` or equivalent file walking: satisfied for `api.py`.
- Broader Cortex targeted tests and `py_compile` pass: satisfied.
- Any remaining stack-related file projection code is documented as trace/repair/debug, not runtime authority: not satisfied.

## Execution Map

- T037 was classified `one_go`.
- R035 records the verification result and discovered gap.
- This check creates one follow-up problem to remove or explicitly isolate `Workspace.resolve_active_scope_path(...)`.

## Stress Test

- The check intentionally widened static search beyond `api.py`, which found the lower-level helper.
- This avoids declaring Phase 3 perfect while a stack-walk helper remains in core workspace code.

## Residual Risk

- Until the follow-up is solved, future maintainers could reuse `Workspace.resolve_active_scope_path(...)` and reintroduce file-walk stack authority.

## Result IDs

- R035
