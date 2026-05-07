# T012: Component Worker Assembly DSL

Status: done
Problem: P012

## Objective

Move worker process assembly out of the registry and into component-level
factory modules while keeping the registry declarative.

## Scope

- `novaic-agent-runtime/task_queue/workers/registry.py`
- New component assembly module(s) under `task_queue/workers/`
- Existing worker source/handler modules as needed for imports only.

## Expected Result

`registry.py` becomes a small spec registry; business handler files remain
lifecycle-free and process assembly is shared component code.

## Verification

- Registry and worker generic tests.
- Static residue guard blocking `_run_*worker` functions in registry.
