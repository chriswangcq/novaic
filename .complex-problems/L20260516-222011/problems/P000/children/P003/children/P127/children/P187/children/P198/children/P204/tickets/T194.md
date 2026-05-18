# Projection test branch inventory ticket

## Problem Definition

Projection tests can either protect the desired shell/display/artifact contract or accidentally keep obsolete payload shapes alive. We need to classify projection tests before cleanup.

## Proposed Solution

Inspect projection-focused tests across Cortex, runtime, and factory. Classify legacy-shape tests as active contract, defensive compatibility guard, test-only fixture, or stale. Do not edit tests in this ticket.

## Acceptance Criteria

- Covers Cortex projection tests, runtime multimodal/projection tests, shell output contract tests, factory multimodal/provider/log tests, and stale helper tests.
- Identifies stale or misleading tests with file/line evidence.
- No code changes.

## Verification Plan

Use `rg` and line-numbered reads to inventory tests and classify each suspicious branch.

## Risks

- Some tests with legacy-looking fixtures may actually guard against reintroducing raw base64 leaks.

## Assumptions

- This ticket is read-only inventory.
