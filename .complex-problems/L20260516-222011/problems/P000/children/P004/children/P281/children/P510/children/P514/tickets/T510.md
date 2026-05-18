# Static Residue Guard Design Ticket

## Problem Definition

P514 must define the static residue guard for risky queue/session/FSM legacy or imperative paths so P512 can run and classify it consistently.

## Proposed Solution

Use targeted source searches over runtime queue/session/FSM code and tests to define guard terms, path scope, and expected hit classes. Save the proposed scan command and classification taxonomy as artifacts.

## Acceptance Criteria

- Guard terms and path scope are explicit.
- Scan command is defined and saved.
- Expected legitimate hit categories are listed for P512.

## Verification Plan

- Inspect the saved guard design artifact.
- Confirm terms cover active-session legacy, direct saga creation, imperative dispatch branching, finalize/recovery ownership, and compatibility remnants.

## Risks

- Guard terms can be too broad and produce noisy live-path hits.
- Guard terms can be too narrow and miss renamed residue.

## Assumptions

- P514 designs the guard; P512 owns running/classifying the final scan.
