# P006: Declarative WorkerSpec Registry

Status: done
Parent: P002
Ticket: T006

## Problem

`WorkerRegistry` centralizes command assembly, but it still contains hundreds
of lines of handwritten assembly functions. The target is mostly declarative
`WorkerSpec` data plus small factories.

## Success Criteria

- Worker modes are declared as `WorkerSpec` data.
- Shared parser/runtime/process assembly is factored into component code.
- Per-worker entries name only options, source factory, handler factory,
  reporter policy, concurrency, cleanup, and startup lines.
- Registry tests prove exact modes and option exposure.

## Subproblems

- [ ] P011: Worker Command Option DSL
- [ ] P012: Component Worker Assembly DSL
- [ ] P013: Worker Registry Residue Closure

## Results

- Split into smaller tickets because a perfect-shape worker registry requires
  data-driven parser options, component-level worker assembly, and explicit
  physical residue cleanup. This should not be treated as a one-step refactor.
- See `../results/R006-declarative-worker-spec-registry.md`.

## Check

- See `../checks/C006-declarative-worker-spec-registry.md`.

## Follow-ups

- Pending.
