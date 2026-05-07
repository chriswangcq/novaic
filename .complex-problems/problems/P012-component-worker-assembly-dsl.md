# P012: Component Worker Assembly DSL

Status: done
Parent: P006
Ticket: T012

## Problem

Even after option data is declarative, `task_queue/workers/registry.py` still
contains per-worker `_run_*` assembly functions. That file should be a registry
of worker specs, while component-level factories build sources, handlers,
runtime, reporters, cleanup, and startup lines.

## Success Criteria

- Registry entries name only declarative worker assembly specs and options.
- Worker assembly implementation lives in component modules, not the registry.
- Adding a worker means adding a spec/factory pair rather than writing bespoke
  process glue inside the registry.
- Existing worker modes still run through `run_sync_worker_process`.

## Result

- See `../results/R012-component-worker-assembly-dsl.md`.

## Check

- See `../checks/C012-component-worker-assembly-dsl.md`.
