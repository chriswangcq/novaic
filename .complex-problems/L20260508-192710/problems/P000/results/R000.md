# Root cause fixed and deployed

## Summary

The repeated smoke failure had two concrete harness-level causes, not an LLM behavior issue:

- `im_reply` counters were stored against the agent-root scope, so historical wake replies accumulated into later wakes and produced false `im_reply cap reached (12/10)`.
- Shell execution paid the cost of materializing the full Cortex RO tree before every command. Production evidence showed Cortex executed a trivial shell command in about 107 ms, while the runtime HTTP request took about 34 seconds and surfaced as `timed out`.
- A secondary hot path made this worse: stack checks called context status in a mode that rendered full LLM context even when only stack depth was needed.

The fix was implemented, deployed, and smoke-tested in production.

## Done

- Runtime now passes `wake_scope_path` into `counter_inc` for `im_reply`, so reply caps are scoped to the current wake instead of agent root.
- Runtime Cortex bridge now budgets shell HTTP timeout as command timeout plus bridge overhead, so storage/setup latency is not misreported as command runtime timeout.
- Cortex `meta_counter_inc` accepts `scope_path` and resolves the actual active/archived wake scope before updating counters.
- Cortex shell sandbox now lazily materializes RO only when the command references RO/root Cortex paths; RW is still materialized normally.
- Cortex shell materialization now fetches store objects with bounded concurrency instead of serial blob reads.
- Cortex context status is stack-only by default; full usage/context rendering is opt-in via `include_usage`.
- Deployed the services with `./deploy services`.

## Verification

- Local runtime tests passed: `PYTHONPATH=.:../novaic-common pytest tests/unit/task_queue/test_environment_tool_handlers.py tests/test_pr186_runtime_main_path_acceptance.py -q` -> 16 passed.
- Local Cortex tests passed: `PYTHONPATH=.:../novaic-common pytest tests/test_sandbox_sync.py tests/test_pr67_wake_child_api.py -q` -> 10 passed.
- Production `./deploy status` showed all primary services healthy and all worker roles at expected counts.
- Production smoke v5 shell path succeeded: wake `230161e4-0412-47b1-9603-dc23d587c1ff` ran `echo smoke-fast-v5 && date`, produced stdout, finalized with `stack_depth=0`, and session returned to `no_active`.
- Production smoke v6 reply-cap path succeeded: wake `c9d4190a-f8c1-4081-9d81-2895f1a54cb9` sent `SMOKE_IM_REPLY_OK_V6`, then `skill_end` succeeded, `cortex.scope_end` finalized with `finalize_reason=stack_empty`, and session returned to `no_active`.

## Known Gaps

- none

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/environment_tool_handlers.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_environment_tool_handlers.py`
- `novaic-agent-runtime/tests/test_pr186_runtime_main_path_acceptance.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/sandbox.py`
- `novaic-cortex/tests/test_pr67_wake_child_api.py`
- `novaic-cortex/tests/test_sandbox_sync.py`
