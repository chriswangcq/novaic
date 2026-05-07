# P009: Saga Launch Engine Extraction

Status: done
Parent: P005
Ticket: T009

## Problem

`SagaLaunchHandler` still owns heartbeat, DAG build, task publish,
mark-launched, and mark-failed protocol. It should only decode a saga job and
delegate to a saga launch adapter.

## Success Criteria

- Saga claim source and handler remain small in `saga_worker.py`.
- Saga heartbeat/DAG publish/mark protocol moves behind `SagaLaunchEngine`.
- Existing saga worker and saga boundary tests pass.
- Tests prove the handler no longer owns DAG publish/heartbeat methods.

## Subproblems

- None initially.

## Results

- R009: Saga launch protocol extracted into `SagaLaunchEngine`.

## Check

- C009: success

## Follow-ups

- None.
