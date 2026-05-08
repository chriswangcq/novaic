# Task/Saga Engine Boundary Guards

## Problem Definition

Task and saga engines have been migrated to effect adapters, but without automated guardrails the old direct-client pattern could be reintroduced later. We need tests that enforce the new boundary instead of relying on code review memory.

## Proposed Solution

Add source/AST-based boundary tests that assert task/saga action engines do not import concrete clients, do not expose old constructor parameters, do not store client attributes, and do not call old protocol methods directly. Also assert worker assembly wires `TaskExecutionEffectAdapter` and `SagaLaunchEffectAdapter` into engine constructors.

## Acceptance Criteria

- Boundary test rejects concrete client imports in `task_execution.py` and `saga_launch.py`.
- Boundary test rejects old concrete-client constructor parameters.
- Boundary test rejects old `self.client`, `self.saga_client`, `self.business_client`, and `self.task_client` ownership attributes.
- Boundary test rejects direct self-owned protocol calls in task/saga engines.
- Boundary test asserts worker assembly wires effect adapters into both engines.
- Focused boundary and task/saga tests pass.

## Verification Plan

- Run the new boundary test.
- Run focused task/saga worker tests already affected by P012/P013.
- Compile worker modules.

## Risks

- Source tests can be brittle if too broad; use AST checks where possible and keep string checks specific to constructor/wiring residue.

## Assumptions

- It is acceptable for adapter modules to import concrete clients; the forbidden boundary is action engine ownership.
