# Safe Active-Surface Semantic Residue Remediation Ticket

## Problem Definition

Discovery `P749/R766` found multiple precise stale or misleading active-surface claims across docs, service code, App resources, generated assets, and frontend/log UI residue. This ticket must remediate those findings without broad speculative cleanup and without leaving generated copies or inactive dangerous UI helpers behind.

## Proposed Solution

Split the remediation by ownership surface so each child can patch and verify a narrow boundary:

- Active docs and architecture wording: Cortex, LogicalFS, Sandboxd, Blob, and data-ownership wording.
- Runtime/Cortex/Business/Device source wording and compatibility cleanup.
- LogicalFS/Sandbox/VMuse service cleanup.
- App resources/generated asset synchronization and backend startup/package graph cleanup.
- App frontend/log UI cleanup around Factory Logs, unused `SmartValue`, and legacy `AssistantMessage` event rendering.

Each child should either implement the safe scoped cleanup or split again if the dependency boundary is unclear.

## Acceptance Criteria

- Safe stale active docs/code comments/scripts are patched to current boundary language.
- Generated resource changes are applied through their source/sync mechanism when needed, or explicitly synchronized with source/resource files when the repo commits generated assets.
- Unsafe or unclear broad cleanup is split into further child problems instead of patched casually.
- Touched files are minimal and scoped to the classified active residue.
- Relevant focused tests/lints are run for each modified surface.

## Verification Plan

Use the remediation backlog from `R766` as the checklist. For each child, inspect the exact files before patching, apply focused changes, run focused tests/lints, and record residual risk. At the parent level, run targeted `rg` checks over the stale terms and review `git diff --stat` for excessive churn.
