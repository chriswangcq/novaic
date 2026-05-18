# Active Docs Final Residue Sweep Ticket

## Problem Definition

After focused architecture/reference/runbook cleanup, a final active-doc sweep is needed to catch unresolved stale guidance.

## Proposed Solution

Run a bounded residue scan over active documentation, classify remaining hits, and either clean or record follow-up for any unresolved active guidance.

## Acceptance Criteria

- Final active-doc scan is run.
- Remaining hits are classified.
- New stale active guidance is cleaned or escalated.
- Verification recorded.

## Verification Plan

- `rg` over active docs excluding roadmap tickets/history-heavy archives where appropriate.
- Focused review of remaining hits.
