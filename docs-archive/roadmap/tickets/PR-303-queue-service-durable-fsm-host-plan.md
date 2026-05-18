# PR-303 — Queue Service Durable FSM Host Plan

Status: Closed

## Goal

Create the controlling phased implementation plan ("file 1") for turning Queue
Service into a durable FSM host across session, task, saga, and worker lease
lifecycles.

## Scope

- Add `docs/architecture/queue-service-durable-fsm-host-plan.md`.
- Create ticket files for every phase before implementation.
- Make each ticket name implementation scope, deletion scope, explicit
  dependency boundary, and verification.

## Out Of Scope

- Runtime code changes belong to PR-304 and later.
- Deployment changes belong to the phase ticket that touches the relevant
  worker or startup path.

## Small Tickets

- [x] **PLAN-01 File 1**: write the phased durable FSM host plan.
- [x] **PLAN-02 Ticket ledger**: create PR-304 through PR-315 ticket files.
- [x] **PLAN-03 Review gate**: verify that every phase has deletion and test
  gates.

## Explicit Dependency Boundary Review

Target: compliant.

This is a documentation ticket. It must not introduce hidden runtime inputs.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- None.

Must be removed by follow-up tickets:

- Task direct status branches: PR-307.
- Saga direct status branches: PR-312.
- Worker direct heartbeat/recovery mutation: PR-313.
- Final queue lifecycle residue: PR-315.

## Verification

- Confirmed `docs/architecture/queue-service-durable-fsm-host-plan.md` exists.
- Confirmed PR-304 through PR-315 ticket files exist.
- Reviewed the master plan: every phase names deletion and verification gates.

## Closure Notes

Created file 1 and the phase ticket ledger. Phase 0 is closed; Phase 1 starts
with PR-304 and PR-305.
