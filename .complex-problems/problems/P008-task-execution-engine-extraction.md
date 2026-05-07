# P008: Task Execution Engine Extraction

Status: done
Parent: P005
Ticket: T008

## Problem

`TaskExecutionHandler` still contains heartbeat, idempotency guard,
retry/fail/complete protocol, and handler invocation details. This makes the
business handler a process-shaped implementation instead of a small job DSL
boundary.

## Success Criteria

- Task queue source and handler remain in `task_worker.py`.
- Task execution protocol moves behind an explicit `TaskExecutionEngine`.
- Handler `handle(job)` decodes the job and delegates to the engine.
- Existing idempotency, retry, business error, and high-concurrency replay
  tests still pass.
- Tests prove the handler no longer owns heartbeat/idempotency protocol
  methods.

## Subproblems

- None initially.

## Results

- R008: Task execution protocol extracted into `TaskExecutionEngine`.

## Check

- C008: success

## Follow-ups

- None.
