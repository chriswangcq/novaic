# Active docs and scripts semantic residue discovery ticket

## Problem Definition

Active docs and operational scripts may still contain stale service-boundary claims after recent architecture changes. This ticket must discover and classify those claims without modifying product files.

## Proposed Solution

Run focused scans over docs and scripts for boundary-sensitive terms and old architecture phrasing. Sample relevant files with context, classify findings, and list exact remediation candidates for the later remediation child.

## Acceptance Criteria

- Active docs/scripts are scanned for service-boundary terms.
- Findings are classified as current, historical, generated/reference-only, or stale remediation candidates.
- Exact remediation candidates are listed.
- No product docs/scripts are changed in this ticket.

## Verification Plan

Use `rg` scans and `git diff --name-only`/`git diff --stat` to verify discovery did not patch product files.
