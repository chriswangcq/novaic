# Diagnose slow execution from backend evidence

## Problem Definition

Execution feels slow. The backend has multiple possible contributors: queue backlog, Runtime worker role split, LLM latency, Cortex prepare/append, Device proxy/PC client, or huge log files causing IO pressure. Need collect enough production evidence to localize the bottleneck.

## Proposed Solution

Create bounded backend probes: status, DB task timing summaries, recent slow tasks by topic, current queue backlog, targeted log snippets around current time, and direct device proxy timing. Then classify where the delay occurs.

## Acceptance Criteria

- Report current service/worker health.
- Report recent queue task backlog and slow tasks by topic.
- Report direct HD tool timing for shell/screenshot/mouse if relevant.
- Report whether giant logs or noisy logging are likely contributing.
- Provide a concrete conclusion and next fix recommendation.

## Verification Plan

- Use remote SQL against queue DB if available.
- Use bounded `tail`, `grep`, and Python parsing; avoid full-file scans.
- Compare direct Device proxy timing with queue/runtime task timing.

## Risks

- Production DB schema may differ; adapt by introspection.
- Some user-visible slowness may be in app/frontend polling rather than backend execution.

## Assumptions

- The slow execution refers to the recent agent/tool execution path after the mounted Host Desktop tool deployment.
