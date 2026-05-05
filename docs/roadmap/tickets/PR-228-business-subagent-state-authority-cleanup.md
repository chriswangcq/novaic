# PR-228 — Business Subagent State Matrix Authority Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Entangled authority boundary |
| Created | 2026-05-05 |
| Scope | `novaic-business/business/internal/subagent_state.py` and tests |
| Dependencies | PR-168E, PR-225 |

## Goal

Remove the duplicate Business-side transition matrix as an apparent source of
truth. Entangled owns transition validation; Business should only send transition
requests and translate Entangled errors.

## Small Tickets

### PR-228A — Remove Business Matrix Export

- Objective: stop exporting `ALLOWED` from Business.
- Scope: Business subagent state module and direct imports.
- Expected result: callers cannot accidentally treat Business as transition-rule
  authority.
- Verification: targeted `rg` and Business subagent tests.

### PR-228B — Reframe Tests Around Client Boundary

- Objective: delete tests that pin the duplicate matrix and keep tests that pin
  request shape/error translation.
- Scope: Business subagent state tests.
- Expected result: tests verify Business as a client boundary, not as canonical
  state-machine owner.
- Verification: run focused Business tests.

## Acceptance

- No live Business export named `ALLOWED`.
- No Business test asserts transition-matrix contents.
- Business transition helpers still pass request-shape and error-mapping tests.

## Closure

Closed 2026-05-05. Business no longer exports `ALLOWED`; transition rules are
documented and tested as Entangled authority, while Business tests cover request
shape and error translation.
