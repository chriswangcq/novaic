# T006: Declarative WorkerSpec Registry

Status: done
Problem: P006

## Objective

Collapse handwritten registry assembly into declarative WorkerSpec entries.

## Scope

- Worker registry.
- Component-level worker spec/factory code.
- Registry tests.

## Expected Result

Adding a worker means adding a spec, not writing a bespoke `_run_xxx_worker`.

## Verification

- Registry mode/option tests.
- Static tests that block per-worker assembly functions.
- Full runtime tests.

## Execution Notes

- Closed through P011/P012/P013. See P006 result and check files.
