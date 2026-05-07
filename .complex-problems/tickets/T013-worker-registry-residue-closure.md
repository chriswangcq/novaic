# T013: Worker Registry Residue Closure

Status: done
Problem: P013

## Objective

Delete stale tests/docs/contracts that still describe the pre-DSL registry
shape, and add guards for the new shape.

## Scope

- Tests under `novaic-agent-runtime/tests/`
- P006/P002 ledger closure files.

## Expected Result

No test or source path depends on bespoke registry run/configure functions.

## Verification

- `rg "_configure_|_run_.*worker" novaic-agent-runtime/task_queue/workers/registry.py`
  returns no matches.
- Full targeted worker test suite passes.
