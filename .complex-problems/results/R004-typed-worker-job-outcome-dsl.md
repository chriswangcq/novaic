# R004: Result for T004

Ticket: T004
Problem: P004

## Done

- Introduced a generic worker job DSL:
  `WorkerJobSpec(kind, payload_key, payload_type)`.
- Added `decode_worker_job()` so handlers decode accepted job contracts once at
  their boundary.
- Added explicit specs for:
  task ready/dependency-released jobs, saga claimed jobs, health ticks,
  scheduled wake ticks, session outbox drains, and saga outbox drains.
- Replaced raw job construction in task/saga sources and registry synthetic
  jobs with spec constants.
- Added invalid job kind/payload tests for every migrated handler family.

## Verification

- `python -m compileall -q queue_service/worker queue_service/session_outbox_worker.py queue_service/saga_outbox_worker.py task_queue/workers tests`
- Targeted worker/job contract pytest suite: `56 passed`

## Known Gaps

- Handler outcomes still use `WorkerResult` directly with ad hoc payload maps;
  this is acceptable for P004's job-boundary scope but should be revisited if
  outcome payloads start driving orchestration decisions.
- P005 still needs task/saga execution extraction to shrink business code from
  "handler with typed input" toward "small DSL actions".
