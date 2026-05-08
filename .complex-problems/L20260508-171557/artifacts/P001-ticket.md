# Ticket: Implement Worker Assembly Specs

## Problem Definition

`worker_assemblies.py` still owns large hand-written worker construction branches. We need a current-path substrate where worker assembly is declared as specs and the module used by registry is thin.

## Proposed Solution

Introduce `assembly_specs.py` with a `WorkerAssemblySpec` and registry/interpreter. Move the current concrete factory implementations out of `worker_assemblies.py` into `assembly_factories.py`, then make `worker_assemblies.py` expose thin spec-backed wrapper functions for compatibility with the command registry.

## Acceptance Criteria

- `worker_assemblies.py` is spec-backed and no longer contains direct client/engine/handler lifecycle construction.
- `assembly_specs.py` owns the generic assembly spec/interpreter.
- Existing runtime worker modes still resolve through the same public `assemble_*` functions.
- Tests prove specs cover every `RUNTIME_WORKER_MODES` mode and old direct lifecycle construction is absent from `worker_assemblies.py`.

## Verification Plan

- Run targeted worker registry/assembly tests.
- Run runtime supervision lint.
- Inspect `worker_assemblies.py` to confirm it is thin and spec-driven.

## Risks

- Existing tests may assert old source text in `worker_assemblies.py`; update them to match the new intended architecture.
- Moving factories must preserve public wrappers and `_connect_db_with_schema_retry` for existing tests.

## Assumptions

- Concrete factory code may remain in `assembly_factories.py` temporarily while later tickets reduce action engines and policies. The key closure for this ticket is that the registry-facing assembly module is data/spec-backed.
