# T002: Business-Only DSL Worker Architecture

Status: done
Problem: P002

## Objective

Drive runtime workers toward the perfect shape where business modules define
small DSL/spec units and infrastructure owns worker lifecycle, execution
protocols, and state advancement.

## Scope

- `novaic-agent-runtime/task_queue/workers/*`
- `novaic-agent-runtime/queue_service/worker/*`
- `novaic-agent-runtime/task_queue/workers/registry.py`
- targeted worker/FSM tests
- architecture and complex-problem ledger files

## Expected Result

The parent problem is split into ordered, verifiable phase problems. Parent
closure requires every subproblem to close with concrete checks.

## Verification

- Every subproblem has a result and check file.
- Parent check maps every success criterion to evidence.
- Runtime full suite passes.

## Execution Notes

- Started 2026-05-07.
- Prediction: not one-go. The problem mixes lifecycle cleanup, typed contracts,
  task/saga protocol extraction, registry shape, and residue deletion.
