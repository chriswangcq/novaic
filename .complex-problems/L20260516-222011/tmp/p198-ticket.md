# Projection branch inventory ticket

## Problem Definition

Projection-related branches are spread across Cortex result projection, runtime context/message preparation, shell output contracts, display handling, and tests. Before cleanup, we need a precise inventory and classification so stale branches are removed deliberately rather than guessed at.

## Proposed Solution

Run targeted repository searches over projection keywords and inspect the relevant production/test files. Build a classification table for suspicious branches and identify exact cleanup candidates for later child problems. Do not edit production or test code in this ticket.

## Acceptance Criteria

- Inventory includes Cortex projection, runtime projection/message preparation, factory/provider/log projection, shell output contract, and test coverage.
- Suspicious branches are classified as active, test-only, compatibility, or stale.
- Cleanup candidates include exact file/line evidence.
- Result distinguishes "active because current path uses it" from "compatibility because persisted data may still contain it".

## Verification Plan

Use `rg`, `sed`, and targeted file reads to inspect production and tests. The result itself is the artifact for downstream cleanup tickets.

## Risks

- A branch can look stale but still be needed for persisted historical step results.
- Tests can intentionally model malformed historical data; these should be classified as defensive coverage rather than stale without evidence.

## Assumptions

- No code changes are allowed in this inventory ticket.
- Follow-up cleanup tickets will handle removals.
