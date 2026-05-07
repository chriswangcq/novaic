# P011: Worker Command Option DSL

Status: done
Parent: P006
Ticket: T011

## Problem

`WorkerRegistry` still accepts arbitrary configure callbacks for each worker.
That keeps CLI option exposure as executable business-ish branching instead of
declarative data.

## Success Criteria

- Worker commands expose options through immutable option specs.
- `WorkerRegistry.build_parser()` has one generic option application path.
- No `_configure_*` functions remain in `task_queue/workers/registry.py`.
- Registry tests prove expected modes and option exposure.

## Result

- See `../results/R011-worker-command-option-dsl.md`.

## Check

- See `../checks/C011-worker-command-option-dsl.md`.
