# Verify skill lifecycle cutover boundaries result

## Summary

Audited skill lifecycle cutover boundaries after P038/P039. Focused and full tests pass, but the audit found a real remaining direct-only lifecycle bypass: the older JWT `/v1/skill/begin` and `/v1/skill/end` endpoints still call `Cortex.skill_begin/end`, which directly uses `Workspace.create_scope/complete_child_scope` without `SkillScopeOpened/Closed` events.

## Done

- Ran focused lifecycle event tests.
- Ran full Cortex suite.
- Scanned lifecycle write sites including:
  - `context_skill_begin`;
  - `context_skill_end`;
  - `Workspace.create_scope`;
  - `Workspace.complete_child_scope`;
  - `summary.md`, child scope index, and meta phase writes;
  - older runtime skill lifecycle entrypoints.
- Classified write sites:
  - `/v1/context/skill_begin` is event-wired by P038.
  - `/v1/context/skill_end` is event-wired by P039.
  - `Workspace.create_scope` / `complete_child_scope` are transitional filesystem projections when reached from context endpoints.
  - `Workspace.create_scope` also initializes child scope index rows and meta files, which remain transitional.
  - `Runtime.skill_begin/end` behind `/v1/skill/begin` and `/v1/skill/end` are direct-only bypasses and need a follow-up.

## Evidence

- Focused tests: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_writer.py tests/test_context_event_projection.py -q` → `38 passed`.
- Full suite: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `449 passed`.
- Static scan found:
  - `novaic_cortex/api.py:/v1/context/skill_begin` and `/v1/context/skill_end` event-wired paths.
  - `novaic_cortex/api.py:/v1/skill/begin` and `/v1/skill/end` still call `Cortex.skill_begin/end`.
  - `novaic_cortex/runtime.py:Cortex.skill_begin/end` still call `Workspace.create_scope/complete_child_scope` directly.

## Residual Risk

- True direct-only lifecycle bypass remains through the older JWT skill endpoints/runtime methods.
- P040 should not close successful until that bypass is physically removed or redirected through the event-wired context lifecycle path.
