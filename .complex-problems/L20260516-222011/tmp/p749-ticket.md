# Cross-service semantic residue discovery and classification ticket

## Problem Definition

The repository may still contain stale semantic claims about which service owns which responsibility. This discovery ticket must identify and classify such residue without patching it.

## Proposed Solution

Run targeted scans over active docs, scripts, app resources, generated assets, and service code for boundary-sensitive terms and old phrasing. Group findings into active stale candidates, generated/resource copies, historical docs, lower-level protocols, and harmless tests/fixtures. Produce an exact remediation candidate list for the next child problem.

## Acceptance Criteria

- Scans cover Cortex, Gateway, Business, Device/devicectl, Queue, Runtime, Blob, LogicalFS, Sandboxd, shell, display, VMuse, and VmControl terms.
- Findings are classified by file/surface and risk.
- Safe remediation candidates are explicit enough to patch without re-auditing.
- No code/docs are modified in this discovery ticket.

## Verification Plan

Use `rg` scans with context and summarize evidence into a result file. Confirm with `git diff --stat` or equivalent that this discovery ticket did not modify product files.
