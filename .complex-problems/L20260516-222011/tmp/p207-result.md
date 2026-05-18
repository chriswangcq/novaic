# `resolve_for_llm` caller/export inventory result

## Summary

Fresh static inventory confirms `resolve_for_llm` has no live production callers in the repository. It is exported from `novaic_cortex.__init__` and used only by its stale dedicated test file.

## Evidence

- `rg -n "resolve_for_llm|step_result_projection" -S .` found production mentions in:
  - `novaic-cortex/novaic_cortex/step_result_projection.py`: docstring, section comment, and function definition.
  - `novaic-cortex/novaic_cortex/__init__.py`: import and `__all__` export.
  - `novaic-cortex/novaic_cortex/api.py`: imports `parse_tool_result`, `preview_for_text`, and formatter functions from `step_result_projection`, but not `resolve_for_llm`.
- `rg -n "resolve_for_llm" novaic-cortex novaic-agent-runtime novaic-llm-factory novaic-common docs -S` found no runtime/factory/business/common callers.
- The only direct non-production caller is `novaic-cortex/tests/test_resolve_for_llm.py`.

## Deletion Targets

- Remove `resolve_for_llm` from `novaic-cortex/novaic_cortex/step_result_projection.py`.
- Remove `resolve_for_llm` import and `__all__` entry from `novaic-cortex/novaic_cortex/__init__.py`.
- Remove now-unused `base64` import from `step_result_projection.py` if no remaining code needs it.
- Delete or replace `novaic-cortex/tests/test_resolve_for_llm.py` in test cleanup.

## External Export Risk

`resolve_for_llm` is currently part of the package root `__all__`, so external code could import it from `novaic_cortex`. Within this monorepo, no such caller exists. Given the user's stated preference for no backwards-compatible residue and the known unsafe base64-inline behavior, removal is justified.

## Code Changes

None. This was a read-only inventory ticket.
