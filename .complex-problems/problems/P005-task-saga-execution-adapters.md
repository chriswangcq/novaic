# P005: Task And Saga Execution Protocol Adapters

Status: done
Parent: P002
Ticket: T005

## Problem

Task and saga handlers still own infrastructure protocol: heartbeat,
idempotency, retry, complete/fail, publish DAG tasks, and mark launched/failed.

## Success Criteria

- Task execution protocol is extracted into an explicit adapter/engine.
- Saga launch protocol is extracted into an explicit adapter/engine.
- Business computation units return domain outcomes.
- Queue state advancement remains through Queue Service clients/FSM endpoints.
- Tests cover success, business failure, retryable failure, idempotency
  duplicate/in-progress, saga launch success/failure.

## Subproblems

- P008: Task Execution Engine Extraction
- P009: Saga Launch Engine Extraction
- P010: Execution Adapter Residue Audit

## Results

- R005: Task and saga execution protocols extracted into explicit engines.

## Check

- C005: success

## Follow-ups

- P006: Declarative worker spec registry remains active for parent P002.
