# Scan Runtime Old Path Residue

## Problem Definition

The new runtime path is deployed, but old worker/action/handler branches could still exist as hidden active paths. The audit needs concrete source evidence rather than trusting the previous refactor.

## Proposed Solution

Run targeted source scans and inspect any suspicious matches across runtime workers, action engines, task handlers, startup entrypoints, and Queue Service session/FSM surfaces. Classify matches as accepted infrastructure, test/documentation residue, or active old-path risk.

## Acceptance Criteria

- Direct effect execution residue is scanned in action engines.
- Handler lifecycle and queue DB ownership leakage is scanned.
- Bespoke worker loops and startup dispatch residue are scanned.
- Compatibility/fallback/no-generation surfaces are scanned and classified.
- Any active risk is fixed or converted into a follow-up problem.

## Verification Plan

- Use `rg` scans over the relevant runtime source paths.
- Inspect matched files with bounded slices.
- Run focused tests/lints if any code is changed.

## Risks

- Keyword scans can produce false positives; every suspicious match must be classified with file context.

## Assumptions

- Accepted generic worker loops and explicit compatibility mentions in tests/docs are not automatically failures.
