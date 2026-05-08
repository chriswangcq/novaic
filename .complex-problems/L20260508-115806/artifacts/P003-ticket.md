# P003 Ticket - Effect Adapter And Assembly Guardrails

## Problem Definition

The new effect-plan engines and helper-backed assemblies are valuable only if future edits cannot silently move concrete clients, worker lifecycle constructors, or hidden side effects back into business engines or business assembly. Existing tests cover part of the boundary, but P003 must make the guardrails explicit and harder to regress.

## Proposed Solution

Add or strengthen guardrail tests that verify:

- Business engines only depend on `EffectExecutor` plans and do not own concrete protocol clients.
- Effect adapter modules are the approved place for concrete external clients.
- `worker_assemblies.py` wires explicit adapters and helper builders, but does not construct worker lifecycle primitives.
- `assembly_helpers.py` is the approved infrastructure location for generic worker construction primitives and remains business-agnostic.
- Tests fail on old direct construction and direct protocol-call residue.

## Acceptance Criteria

- Guardrail tests cover task, saga, health, and scheduler action engines.
- Guardrail tests cover assembly helper usage and absence of direct lifecycle constructors in business assembly.
- Guardrail tests distinguish allowed infra modules from forbidden business modules.
- Existing focused tests still pass.
- Compile checks pass.

## Verification Plan

- Run guardrail tests.
- Run focused action-engine and assembly tests.
- Run compile checks for worker modules.
- Use residue searches to prove forbidden construction/call patterns are absent.

## Risks

- Overly broad text guards can block valid infra code; tests must distinguish `assembly_helpers.py` from `worker_assemblies.py`.
- Under-broad guards could miss old paths; include both AST/source guards and focused behavior tests.

## Assumptions

- The P001/P002 implementation is present.
- Concrete effect adapters are allowed to own clients because they are explicit dependency boundaries.
