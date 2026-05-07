# T011: Worker Command Option DSL

Status: done
Problem: P011

## Objective

Replace per-worker argparse configure functions with declarative option data.

## Scope

- `novaic-agent-runtime/task_queue/workers/registry.py`
- Registry parser tests.

## Expected Result

Adding or changing a worker CLI option means editing a `WorkerOption` entry, not
writing a new callback branch.

## Verification

- `pytest -q tests/test_pr337_worker_command_registry.py`
- Static assertion that `_configure_` functions are absent from registry.
