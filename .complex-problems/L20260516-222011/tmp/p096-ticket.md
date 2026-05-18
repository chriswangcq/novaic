# MCP Scripts CI Final Residue Sweep Ticket

## Problem Definition

After MCP and scripts/CI cleanup, a final sweep is needed to confirm there are no obvious unresolved stale residues in those surfaces.

## Proposed Solution

Re-run bounded residue scans across MCP, scripts, and CI helper surfaces; classify remaining hits and run representative verification.

## Acceptance Criteria

- Final residue scan is run over MCP/scripts/CI surfaces.
- Remaining hits are classified.
- New stale residue is either cleaned or converted into a follow-up.
- Verification is recorded.

## Verification Plan

- `rg` final sweep over the bounded surfaces.
- Re-run representative checks touched by cleanup.
