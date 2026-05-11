# Agent loop stalls after one round

## Problem

The deployed backend appears to get stuck after running one agent loop: user-visible Agent Monitor shows a loop executed, then no timely progress or reply. We need determine the concrete runtime cause from live service state, logs, queue database, and relevant code, then fix and deploy it without guessing.

## Success Criteria

- Identify the exact stuck state and root cause with evidence from live backend state/logs and code.
- Implement a focused fix that prevents the agent loop from stalling after one round.
- Remove or avoid any misleading fallback/compat path that would hide the issue.
- Verify locally with targeted tests and remotely with a real deployed smoke/e2e path.
- Commit, deploy, and report residual risk clearly.
