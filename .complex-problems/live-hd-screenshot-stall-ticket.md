# Diagnose production HD screenshot wake stall

## Problem Definition

The latest production agent wake appears to stop after a tool step labeled “尝试 HD 截图 完成”. Backend processes are healthy, so the likely issue is a workflow state transition, tool result interpretation, queue/saga task state, Cortex stack/finalize state, or frontend projection.

## Proposed Solution

Inspect production logs and durable state for the affected user/agent around the screenshot timestamp. Trace from Environment message dispatch to session state, saga DAG tasks, tool result save, react_actions decision, Cortex stack status, and final user reply projection. If the trace reveals a code/config bug, patch the active code path and verify with tests and production smoke. If the trace reveals an operational stuck row, recover it and document the exact reason.

## Acceptance Criteria

- Production evidence identifies the stuck wake/session/saga/task IDs.
- The root cause is tied to a specific state transition or service boundary.
- Any fix is applied to the active path, not a side branch.
- Tests or production smoke prove the wake can progress past the failing point.
- Remaining risks are explicit.

## Verification Plan

- Run remote state/log queries against Queue, Runtime, Cortex, Business, and relevant worker logs.
- Query session/saga/task rows for the affected agent/user and newest wake.
- If code changes are made, run targeted and full tests for affected repos.
- Deploy and run a smoke message/tool path if required.

## Risks

- Production DB schema names may differ; inspect schema before querying.
- The UI card may be stale while backend is complete; verify both backend state and frontend-visible messages.
- Avoid destructive recovery unless the exact stuck state is known.

## Assumptions

- User’s screenshot corresponds to the currently selected 小马 agent.
- SSH/deploy credentials from the repo are valid for read-only production inspection.
