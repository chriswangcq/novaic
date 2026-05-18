# context.jsonl helper implementation success check

## Summary

Success. `R133` maps all requested helpers and fixes a local integrity bug: corrupt materialized context projections now fail visibly instead of dropping lines.

## Evidence

- Helper implementation pointers: `workspace.py:856-907`.
- `read_context` now raises `ValueError` on corrupt JSONL.
- Regression test: `test_read_context_rejects_corrupt_jsonl_projection`.
- Verification: `38 passed in 0.34s`.

## Criteria Map

- Five helpers mapped: satisfied.
- Each helper classified by behavior: satisfied in `R133`.
- Raw payload persistence risk: helper layer writes whatever callers pass; no helper internally expands payloads, and caller/authority risks are delegated to sibling P153/P154.

## Execution Map

- One-go result inspected source, found a concrete silent-corruption bug, patched it, added a test, and reran context projection/read-model suites.

## Stress Test

- The new test writes a mixed valid/corrupt `context.jsonl`, proving projection corruption cannot be silently hidden.

## Residual Risk

- Non-blocking for P152: caller classification remains intentionally outside this helper-only leaf.

## Result IDs

- `R133`
