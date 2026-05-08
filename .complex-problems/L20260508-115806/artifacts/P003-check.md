# P003 Check - Effect Adapter And Assembly Guardrails

## Summary

P003 is solved. Guardrail tests now protect both action-engine effect boundaries and worker assembly helper boundaries.

## Evidence

- Boundary test file now checks engines, adapters, assembly, and helper substrate.
- Guardrail and focused suites pass.
- Compile checks pass.
- Residue search confirms no direct lifecycle construction in `worker_assemblies.py`.

## Criteria Map

- Guardrails cover task, saga, health, scheduler action engines -> satisfied.
- Guardrails cover assembly helper usage and absence of direct lifecycle constructors -> satisfied.
- Guardrails distinguish allowed infra modules from forbidden business modules -> satisfied.
- Existing focused tests pass -> satisfied.
- Compile checks pass -> satisfied.

## Execution Map

- T016 -> R015: guardrail implementation and verification.

## Stress Test

- Moving `TaskQueueClient` or `httpx` back into engines would fail boundary tests.
- Reintroducing raw `GenericWorker` or `SyntheticJobSource` construction in `worker_assemblies.py` would fail guardrails.
- Importing business modules into `assembly_helpers.py` would fail guardrails.

## Residual Risk

- none for P003.

## Result IDs

- R015

## Blocking Gaps

- none
