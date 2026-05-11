# Query production state for stuck HD screenshot wake

## Problem Definition

We need exact production state for the latest 小马 wake that shows HD screenshot tool completion but no final answer.

## Proposed Solution

Use remote logs and SQLite schemas to locate recent messages containing “再试一下”, “HD 截图”, and the corresponding queue/session/saga/task rows. Inspect logs from runtime workers, queue service, Cortex, sandboxd, Business subscriber, and database tables as needed.

## Acceptance Criteria

- Identify newest relevant scope/session/saga/task/outbox IDs.
- Summarize current state and last transition.
- Capture exact evidence pointers from remote logs or DB query output.

## Verification Plan

- Run read-only remote log searches.
- Inspect DB schema before querying tables.
- Cross-check IDs across at least two sources.

## Risks

- Logs may be large; use bounded grep/tail.
- Message text may be truncated; use timestamps and IDs.

## Assumptions

- Production logs live under `/opt/novaic/data/logs`.
- Production DBs live under `/opt/novaic/data` or service-local configured paths.
