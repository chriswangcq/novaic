# Ticket: Audit Business DSL Purity Gap

## Problem Definition

The runtime path is live, but the user asks whether the system is now “pure DSL”. We need to audit where business behavior is declarative/spec-driven versus where hand-written Python still owns branching, retries, effects, and orchestration decisions.

## Proposed Solution

Inspect the worker assembly layer, action engines, effect adapters, generic worker substrate, and business handler modules. Quantify the shape with file/line pointers and grep counts. Run the targeted effect-boundary and assembly tests. Classify the current architecture against the target “business only DSL, component layer owns generic employee mechanics”.

## Acceptance Criteria

- Identify which files are already declarative DSL-like specs.
- Identify which files are still hand-written business/process orchestration code.
- Identify whether effects are plan-first DSL, direct imperative execution, or a mixed state.
- Provide an explicit “pure DSL / not pure DSL” judgment with evidence.
- Avoid implementation changes; this is an audit ticket only.

## Verification Plan

- Inspect `worker_assemblies.py`, `assembly_helpers.py`, action engines, effect adapters, and business handlers with `rg`, `nl`, and `wc`.
- Search for `execute_effect`, `EffectPlan`, `WorkerSpec`, `assemble_`, and engine classes.
- Run targeted tests covering effect boundaries and assembly helpers.
- Record a result with a gap classification and concrete file pointers.

## Risks

- Some code is intentionally component infrastructure, not business logic; the audit must separate acceptable substrate code from business-specific orchestration residue.
- A “pure DSL” claim is easy to overstate if generic workers are present but business engines remain imperative.

## Assumptions

- The target is not zero Python code overall; it is that business behavior should be expressed primarily as specs/DSL and generic component infrastructure should be stable and reusable.
