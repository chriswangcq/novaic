# Document Runtime FSM/Worker DSL Status

## Problem Definition

The runtime FSM and worker refactor now has multiple concrete substrate layers, but the durable architecture documentation must accurately describe the implemented shape. Without a precise status note, future work can drift back into either stale imperative paths or misleading "pure DSL complete" claims.

## Proposed Solution

Add a dedicated architecture status document for the runtime FSM/worker DSL model and link it from the architecture overview. The document will name the live code paths for the worker roster, assembly specs, plan-first effect runner, handler metadata, domain FSMs, and accepted Python computation hooks. It will explicitly distinguish the implemented spec/plan-driven runtime from a hypothetical data-only DSL.

Add a small documentation guard test that checks the status document exists, references the live code paths, and avoids stale completion language.

## Acceptance Criteria

- A durable architecture note describes the current runtime FSM/worker/DSL shape.
- The note references the live roster/FSM path, plan-first effect boundary, assembly specs, handler metadata, and accepted non-DSL computation hooks.
- The architecture overview links to the status note.
- A targeted test guards the document against missing key paths and premature pure-DSL completion wording.
- Targeted tests and runtime supervision/generated-artifact lints pass.

## Verification Plan

- Run the new documentation guard test.
- Run the generated artifact hygiene test.
- Run runtime worker supervision lint.
- Run generated artifact lint.
- Inspect the document for explicit status language and residual-risk honesty.

## Risks

- Documentation could overstate the architecture and hide remaining Python computation hooks.
- A test that is too broad could become brittle; keep it focused on durable status assertions and live path pointers.

## Assumptions

- The desired final shape is spec/plan-driven worker runtime with explicit accepted hooks, not a claim that all business behavior is already data-only.
- Existing design documents remain useful historical context; this ticket adds an authoritative current-status note rather than rewriting the whole docs tree.
