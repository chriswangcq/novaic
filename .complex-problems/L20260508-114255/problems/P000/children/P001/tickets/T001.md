# Audit Generic FSM Worker Substrate Boundaries

## Problem Definition

Audit whether the generic worker/FSM substrate is a clean infrastructure layer: it should own process lifecycle, polling, concurrent execution, reporting, sources, retry/policy concerns, and command assembly without embedding domain-specific business decisions.

## Proposed Solution

Inspect the substrate and assembly code:

- `queue_service/worker/*`
- `task_queue/workers/command_specs.py`
- `task_queue/workers/process_runner.py`
- `task_queue/workers/registry.py`
- `task_queue/workers/worker_assemblies.py`
- related FSM store/state code under `queue_service/fsm`

Look for explicit dependency boundaries, generic contracts, lifecycle ownership, and leakage of task/saga/session-specific details into the reusable substrate.

## Acceptance Criteria

- List substrate files and their responsibilities.
- Identify whether the substrate itself is generic or business-coupled.
- Identify remaining boundary gaps, especially in assembly code.
- Provide concrete evidence pointers.

## Verification Plan

- Use `find`, `rg`, `sed`, and line-count scans.
- Search for business/domain tokens inside `queue_service/worker`.
- Inspect assembly layer separately from substrate.

## Risks

- Assembly code may be intentionally application-specific; do not misclassify it as substrate unless it lives in the reusable layer.

## Assumptions

- `queue_service/worker` is intended to be the reusable component substrate.
- `task_queue/workers/worker_assemblies.py` is allowed to know application services, but should ideally become thinner over time.
