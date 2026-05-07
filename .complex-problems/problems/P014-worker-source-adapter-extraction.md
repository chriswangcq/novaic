# P014: Worker Source Adapter Extraction

Status: done
Parent: P002
Ticket: T014

## Problem

`task_worker.py` and `saga_worker.py` still carry `TaskQueueJobSource` and
`SagaClaimSource`. These are component source adapters, not business
computation DSL. Leaving them inside business handler modules makes the boundary
look fuzzier than it is.

## Success Criteria

- Task/saga source adapters live in component source modules.
- Business handler modules only expose job specs, handler classes, and
  business/engine delegation.
- Assembly imports source adapters from component modules.
- Tests assert source adapters are physically absent from business handler
  files.

## Result

- See `../results/R014-worker-source-adapter-extraction.md`.

## Check

- See `../checks/C014-worker-source-adapter-extraction.md`.
