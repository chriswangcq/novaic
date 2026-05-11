# Inspect live queue/runtime stall evidence

## Problem Definition

We need identify the current production stuck state after an agent loop ran once. The work is read-only diagnosis across deployed processes, logs, and queue database state.

## Proposed Solution

Run bounded remote read-only inspections: service status, fresh logs, active queue/session/saga/outbox tables, recent rows ordered by updated timestamps, and code pointers for the observed state. Summarize the concrete root cause and evidence.

## Acceptance Criteria

- A current live stuck state or absence of one is shown from production data.
- Any failing table/worker/session state is named precisely.
- Evidence includes commands/queries and key observations, not vague log claims.
- The diagnosis identifies the code path likely needing repair.

## Verification Plan

- Use `./deploy status` plus SSH read-only log and SQLite queries.
- Avoid modifying production rows.
- Cross-check with local source search for the responsible state transition.

## Risks

- Querying large logs can be slow; restrict to recent tails and selected table columns.
- Stale history can look like current failure; compare timestamps to current service start.

## Assumptions

- Production queue state in `/opt/novaic/data/queue.db` is the current authority for session and worker progress.
