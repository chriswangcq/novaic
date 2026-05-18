# P545 2-4 Hit Low-Density Test Classification

## Source

- Filtered hits: `.complex-problems/L20260516-222011/tmp/p545/two-to-four-hit-test-hits.txt`
- Counts: `.complex-problems/L20260516-222011/tmp/p545/two-to-four-hit-test-counts.txt`
- Hit lines: `.complex-problems/L20260516-222011/tmp/p545/two-to-four-hit-test-lines.txt`

## Totals

- Hits: 43
- Files: 17

## Classification Table

| File | Hits | Purpose | Classification | Follow-up |
| --- | ---: | --- | --- | --- |
| `tests/test_pr236_session_fsm_decision.py` | 4 | Session FSM decision state setup | Expected boundary coverage for active/no-active session decision inputs. | No |
| `tests/test_pr243_inbox_restart_cutover.py` | 4 | Inbox restart cutover | Expected regression coverage for `remaining_stack` and active-session cleanup after restart. | No |
| `tests/integration/test_depends_on_prev_result.py` | 3 | DAG dependency integration | Expected integration coverage for `queue.publish(... depends_on=...)`. | No |
| `tests/test_finalize_summary_boundary.py` | 3 | Finalize summary boundary | Expected coverage that structural finalize carries explicit stack but not summary text. | No |
| `tests/test_pr277_session_outbox_required_saga_orchestrator.py` | 3 | Outbox publish boundary guard | Expected source guard ensuring publish lives only in session outbox, not repo/wake plan. | No |
| `tests/test_pr306_taskqueue_fsm_cutover.py` | 3 | TaskQueue FSM cutover | Expected queue substrate regression coverage for publish/retry/cancel state paths. | No |
| `tests/test_pr43_last_scope_wiring.py` | 3 | Retired legacy last-scope path | Expected regression coverage that legacy `last_scope_id` inputs do not reintroduce old behavior. | No |
| `tests/test_pr235_session_ledger.py` | 2 | Session ledger projection | Expected ledger coverage for `remaining_stack` and active-session read projection. | No |
| `tests/test_pr237_session_outbox_observe.py` | 2 | Session outbox observe | Expected regression coverage for finalize stack and active recovery saga state. | No |
| `tests/test_pr270_session_finalize_ledger_boundary.py` | 2 | Finalize ledger boundary | Expected coverage that finalize events preserve explicit `remaining_stack`. | No |
| `tests/test_pr284_session_event_vocabulary.py` | 2 | Event vocabulary guard | Expected guard ensuring public vocabulary exists and private string constants do not leak. | No |
| `tests/test_pr313_worker_lease_cutover.py` | 2 | Worker lease cutover | Expected queue publish coverage for worker lease state paths. | No |
| `tests/test_pr48_turn_finalizer.py` | 2 | Turn finalizer payload | Expected coverage that react action/finalizer context carries `remaining_stack`. | No |
| `tests/test_pr57_prev_scope_history_inject.py` | 2 | Retired recap/history injection | Expected source guard that old legacy recap/env flag paths remain absent. | No |
| `tests/test_pr65_agent_root_scope.py` | 2 | Agent root scope archive | Expected scope-end bridge coverage carrying `remaining_stack`. | No |
| `tests/test_pr67_wake_child_scope.py` | 2 | Wake child scope archive | Expected scope-end bridge coverage carrying `remaining_stack`. | No |
| `tests/test_pr85_llm_context_smoke_guardrails.py` | 2 | LLM context smoke guardrail | Expected negative assertion that legacy context projection text is not injected. | No |

## Conclusion

All 2-4-hit low-density tests are expected boundary, integration, or negative guardrail coverage. No stale or misleading test residue was found in this bucket.
