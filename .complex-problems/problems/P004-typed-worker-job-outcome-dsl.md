# P004: Typed Worker Job And Outcome DSL

Status: done
Parent: P002
Ticket: T004

## Problem

Worker sources and handlers still communicate through loosely documented dict
payloads. This hides contracts in code paths and keeps handlers from being
small declarative specs.

## Success Criteria

- Task, saga, scheduler, health, and outbox jobs have explicit job/outcome
  specs or typed envelopes.
- Handler entrypoints decode once at the boundary.
- Tests cover invalid job kind/payload behavior through typed contracts.

## Subproblems

- None.

## Results

- R004: Typed worker job specs and boundary decoding implemented.

## Check

- C004: success

## Follow-ups

- P005: Task/Saga execution adapter extraction remains for smaller domain
  action bodies.
