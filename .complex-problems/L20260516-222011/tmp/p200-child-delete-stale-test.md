# Delete stale `resolve_for_llm` tests

## Problem

`novaic-cortex/tests/test_resolve_for_llm.py` tests the removed `resolve_for_llm` helper and asserts the obsolete inline-image/base64 behavior. It should be physically deleted.

## Success Criteria

- The stale test file is deleted.
- `rg "resolve_for_llm"` finds no production or test references except ledger/docs notes.
- Focused Cortex tests pass without that file.
