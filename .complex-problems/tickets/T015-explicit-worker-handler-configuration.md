# T015: Explicit Worker Handler Configuration

Status: done
Problem: P015

## Objective

Remove hidden `ServiceConfig` fallback reads and stale sync names from worker
business handlers.

## Scope

- task/saga/health/scheduler worker handlers.
- component assembly injection.
- handler tests and residue guards.

## Expected Result

Handler behavior is reproducible from explicit constructor inputs plus injected
runtime dependencies.

## Verification

- Static scan for `ServiceConfig` in business handler modules.
- Worker handler tests.
- Full runtime tests.
