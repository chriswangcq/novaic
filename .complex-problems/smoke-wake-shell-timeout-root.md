# Smoke Wake Shell Timeout And ImReply Cap Diagnosis

## Problem

Production smoke message `18c14d716c0a` / dispatch repair verification v4 reached Queue and Runtime, but the live agent UI shows the wake repeatedly running shell commands that time out and then hitting `im_reply cap reached (12/10)`. The user suspects Cortex stack maintenance / wake lifecycle logic, not just dispatch.

Diagnose the concrete root cause from production evidence and code: why the wake kept timing out, why `im_reply` cap was already exceeded, whether the Cortex stack/finalize logic failed to close the wake, and what code path needs to change if this is a harness bug.

## Success Criteria

- Trace the production wake scope `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0` and message `18c14d716c0a` through Queue tasks, sagas, Cortex files, and Environment notification state.
- Identify the first deterministic failure mechanism, not only the UI symptom.
- Determine whether the failure is caused by tool execution/shell sandbox, im_reply cap enforcement, Cortex stack/finalize maintenance, LLM behavior, or an interaction between them.
- Provide evidence pointers: DB rows, log snippets, scope files, and source code references.
- If a code fix is required, state the minimal fix direction and whether it should be implemented now.
