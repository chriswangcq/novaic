# Smoke wake shell timeout and reply cap fixed

## Summary

The original failure is solved. The historical `im_reply` cap was caused by counters being written to agent-root metadata instead of wake-scope metadata, and the shell timeout was caused by Cortex sandbox setup materializing the full RO tree on every shell command. Both paths were changed, deployed, and verified with targeted unit tests plus production smoke tests.

## Evidence

- Runtime targeted tests passed: 16 passed.
- Cortex targeted tests passed: 10 passed.
- Deployment status after `./deploy services` showed all backend services and all worker roles healthy.
- Smoke v5 proved the shell path no longer times out for a trivial command and the wake finalizes cleanly.
- Smoke v6 proved a fresh wake can send `SMOKE_IM_REPLY_OK_V6` without hitting the previous `12/10` cap and can close the wake skill cleanly.
- Production session state after v6 was `no_active`, with `active_scope_id=null` and `active_saga_id=null`.

## Criteria Map

- Find the definite cause of the repeated smoke failure -> mapped to two code-level causes: root-scoped reply counter and full RO shell materialization.
- Fix code, deploy, and smoke test -> mapped to runtime and Cortex code changes, `./deploy services`, smoke v5, and smoke v6.
- Ensure Cortex stack/session maintenance is clean -> mapped to `skill_end`, `check_stack stack_depth=0`, `cortex.scope_end finalize_reason=stack_empty`, and `session.ended action=session_closed` in production.
- Avoid behavioral/LLM hand-waving -> mapped to direct queue database task/event evidence and targeted unit tests.

## Execution Map

- T000 -> R000: Diagnosed the failure from production queue tasks/events and logs, implemented scoped counters and faster shell sandbox setup, added tests, deployed, and verified production smoke.

## Stress Test

- Failure mode: historical replies from previous wakes poison a new wake's `im_reply` cap. Fixed because `counter_inc` now writes to the concrete wake scope path.
- Failure mode: a command that does not need Cortex RO still times out because RO history is large. Fixed because RO is lazy and only materialized when the command references RO/root paths.
- Failure mode: stack checks stall on full context rendering. Reduced because context status is stack-only by default.
- Failure mode: wake closes but session pointer remains active. Production smoke v5 and v6 both returned `tq_session_state` to `no_active`.

## Residual Risk

- Non-blocking: very large commands that explicitly read `$RO` can still be expensive, but they now request that cost explicitly and get bounded-concurrent materialization.
- Non-blocking: LLM/provider latency can still make a smoke wait, but it is separate from the two harness bugs fixed here.

## Result IDs

- R000

## Blocking Gaps

- none
