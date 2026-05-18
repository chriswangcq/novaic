# Delete `resolve_for_llm` and package export residue

## Problem Definition

The stale `resolve_for_llm` helper remains in production code and can inline image bytes/base64 into text LLM context if revived. Caller inventory proved no live in-repo production usage, so it should be physically deleted.

## Proposed Solution

Remove the helper, its docstring/section comments, its root package import/export, and now-unused imports. Run focused Cortex projection tests and import smoke checks to prove active projection APIs remain intact.

## Acceptance Criteria

- `resolve_for_llm` no longer exists in production code.
- `novaic_cortex.__init__` no longer exports it.
- `step_result_projection.py` has no unused `base64` import or stale helper documentation.
- Active projection tests still pass.

## Verification Plan

Run `rg "resolve_for_llm"` after deletion, then run Cortex projection tests and an import smoke check for active APIs.

## Risks

- A stale test may fail until the separate test cleanup ticket deletes it.
- External users of the old export will break, which is acceptable under the no-backwards-compatible-residue principle.

## Assumptions

- Current repository behavior is represented by active projection tests, not by the stale `test_resolve_for_llm.py` file.
