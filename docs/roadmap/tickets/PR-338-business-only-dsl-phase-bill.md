# PR-338: Business-Only DSL Worker Phase Bill

Status: Closed
Owner: Codex
Problem: P002

## Phase Bill

| Phase | Problem | Goal | Dependency | Verification |
|---|---|---|---|---|
| 9 | P003 | Lifecycle-free business handlers | P001/P003 start | static boundary tests + worker tests |
| 10 | P004 | Typed worker job/outcome DSL | P003 | typed contract tests + runtime tests |
| 11 | P005 | Task/saga execution adapters | P004 | idempotency/retry/saga launch tests |
| 12 | P006 | Declarative WorkerSpec registry | P005 | registry spec tests + runtime tests |
| 13 | P007 | Residue audit and parent closure | P006 | full runtime + parent check |

## Non-Negotiable Constraint

This cannot be solved as one broad patch. Each phase must produce a result file
and a check file before the parent can close.

## Current Closure State

- P003 closed: business handlers are lifecycle-free.
- P004 closed: worker jobs/outcomes use explicit specs.
- P005/P008/P009/P010 closed: task/saga execution protocols live in explicit
  infrastructure engines.
- P006/P011/P012/P013 closed: worker registry is declarative `WorkerSpec` data,
  with concrete process assembly in component factories.
- P007 closed: final residue audit and parent closure.
