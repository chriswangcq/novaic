# Ticket: Fix Canonical Test Matrix LogicalFS Dependency Boundary

## Problem Definition

`scripts/run_all_tests.sh` must encode package dependency boundaries. LogicalFS now imports `common.http.clients`, but the matrix ran it with `PYTHONPATH="."`, causing root verification to fail.

## Proposed Solution

Set the LogicalFS matrix PYTHONPATH to include `../novaic-common` and `../novaic-blob-service`, then rerun the canonical matrix.

## Acceptance Criteria

- LogicalFS matrix step imports `common` successfully.
- `./scripts/run_all_tests.sh` passes all checks.

## Verification Plan

- Run `./scripts/run_all_tests.sh`.

## Risks

- Adding implicit dependencies without recording them would hide a boundary. This ticket explicitly records the dependency in the canonical test matrix.

## Assumptions

- LogicalFS depending on common HTTP client helpers is an intentional infrastructure dependency.
