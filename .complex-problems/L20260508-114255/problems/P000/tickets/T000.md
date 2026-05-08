# Full FSM And Business DSL Gap Audit

## Problem Definition

The user wants a comprehensive audit of the current code against the intended design: a generic FSM/worker substrate with business logic reduced to declarative DSL and small computation handlers. The audit must identify what is already achieved, what still leaks infrastructure into business code, where wiring/deployment/testing gaps remain, and what optimization tickets should exist next.

## Proposed Solution

Split the audit into focused child problems:

- Inspect the generic worker/FSM substrate boundaries and whether they are reusable infrastructure rather than business-specific code.
- Inspect business worker modules for DSL-only shape and residue such as lifecycle loops, clients, hidden dependencies, or direct infrastructure calls.
- Inspect runtime wiring, deployment scripts, and process topology to confirm new code is actually connected and old paths are physically retired.
- Inspect verification coverage, guardrails, and documentation alignment with the desired design.

Then summarize the child results into a root gap report with concrete evidence pointers and next optimization tickets.

## Acceptance Criteria

- The audit names concrete code files and evidence commands.
- The audit distinguishes achieved state from remaining gap.
- The audit includes at least one stress test/failure mode per major area.
- The audit lists next optimization tickets, not vague future work.
- The final check maps all root criteria to evidence.

## Verification Plan

- Use `rg`, `find`, `git status`, line-count scans, and targeted file reads.
- Run existing guard/test commands if needed and affordable.
- Compare business handler files against banned infrastructure/lifecycle tokens.
- Compare deployed/entrypoint scripts against old-path residue.
- Record child problem results and a final success check in the schema-v6 ledger.

## Risks

- Broad audit scope may miss subtle runtime behavior without a live scenario replay.
- Some gaps may be design tradeoffs rather than bugs; classify them explicitly.
- The new ledger itself is temporary audit state and should not be confused with product code.

## Assumptions

- Current working tree represents the latest intended implementation.
- The desired ideal is: generic infrastructure owns lifecycle/source/reporting/process concerns; business layer owns only declarative specs and pure-ish computation handlers with explicit dependencies.
