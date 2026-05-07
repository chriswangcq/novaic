# T017: Task/Saga Handler Engine Injection

Status: done
Problem: P017

## Objective

Move task/saga client and engine construction out of business handler modules.

## Scope

- `task_queue/workers/task_worker.py`
- `task_queue/workers/saga_worker.py`
- `task_queue/workers/worker_assemblies.py`
- task/saga handler tests and boundary guards.

## Expected Result

Task/saga handlers are small typed DSL adapters over injected engines.

## Verification

- Static guard: no Queue/Business client construction in task/saga handler
  modules.
- Task/saga handler tests.
- Full runtime tests.
