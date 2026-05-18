# Step result projection stale branch cleanup result

## Summary

Completed step result projection stale branch cleanup. The work inventoried projection branches, removed stale production/test residue, narrowed/justified retained branches, fixed the Google/Gemini multimodal provider gap discovered by the audit, and passed focused projection regression tests.

## Done

- P198/R190 inventoried Cortex/runtime/factory/test projection branches and identified stale candidates plus the Gemini provider gap.
- P199/R197 removed stale production `resolve_for_llm` helper/export, removed nested `result` unwrapping, and bounded unknown dict fallback.
- P200/R201 deleted stale `test_resolve_for_llm.py`, cleaned misleading guard-test names, and reran focused tests.
- P201/R211 completed the aggressive regression sweep, fixed/tested Gemini multimodal conversion, and classified remaining branches as intentional.

## Verification

- `resolve_for_llm` removed from active production/tests.
- `novaic-cortex/tests/test_resolve_for_llm.py` deleted.
- No active `resolve_for_llm` references remain.
- Cortex projection tests passed: `18 passed in 0.06s` in final focused chain.
- Runtime projection/multimodal tests passed: `10 passed in 0.07s` in final focused chain.
- Factory chat/log tests passed: `17 passed in 0.21s` in final focused chain.
- Remaining projection compatibility branches are classified as current shell/display/history/provider/logging contracts.

## Known Gaps

- No blocking gap remains for this projection cleanup branch. Live Gemini API validation is out of deterministic unit scope.

## Artifacts

- R190
- R197
- R201
- R211
- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-cortex/novaic_cortex/__init__.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_step_result_projection.py`
- `novaic-cortex/tests/test_resolve_for_llm.py` deleted
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- `novaic-llm-factory/factory/providers.py`
- `novaic-llm-factory/tests/test_chat_routes.py`
