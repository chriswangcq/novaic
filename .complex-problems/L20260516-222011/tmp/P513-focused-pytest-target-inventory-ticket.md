# Focused Pytest Target Inventory Ticket

## Problem Definition

P513 needs a focused test target inventory for queue/session/FSM/outbox/finalize verification.

## Proposed Solution

Use `rg --files` and targeted filename/content searches in `novaic-agent-runtime/tests` to identify focused pytest files, then write an artifact that maps each selected file to the behavior it covers and explains notable exclusions.

## Acceptance Criteria

- Discovery commands are recorded.
- Selected focused test files are listed with behavior coverage labels.
- Exclusions or non-selected candidate groups are briefly explained.

## Verification Plan

- Re-run the discovery commands or inspect the saved artifacts.
- Check that the inventory covers dispatch, session state, outbox, finalize, recovery, saga compensation, and FSM decisions.

## Risks

- File names may not fully describe coverage, so targeted content searches are needed in addition to filename matching.

## Assumptions

- This ticket is read-only and does not execute tests.
