# Ticket: Gateway/app edge residue remediation and verification

## Problem Definition
Use P713's boundary map to classify and remediate active Gateway/app edge residue. Patch safe active claims that imply Gateway owns Queue DB, Entangled schema/sync, Business logic, Runtime state, or Device hooks.

## Proposed Solution
Review P713 cleanup candidates and focused scans, classify active vs historical/roadmap/contrast entries, patch bounded active misleading docs/scripts, and verify with focused scans. Split if cleanup expands beyond bounded active docs.

## Acceptance Criteria
- P713 cleanup candidates are dispositioned.
- Safe active Gateway/app edge stale claims are patched.
- Historical roadmap and explicit old-vs-new contrast rows are left untouched but documented.
- Focused scans and relevant lint/tests verify no touched active file preserves the stale claim.

## Verification Plan
Run focused `rg` over active gateway docs/scripts, patch with `apply_patch` if needed, save before/after scans, and run docs/status or boundary lint where relevant.
