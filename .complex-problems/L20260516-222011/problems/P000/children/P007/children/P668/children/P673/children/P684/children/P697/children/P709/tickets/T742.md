# Semantic/app/device service residue cleanup and verification ticket

## Problem Definition

Cross-service docs, scripts, generated assets, and code comments may still contain stale or misleading responsibility claims after the FSM, shell/display, Device/devicectl, LogicalFS, Sandboxd, Blob, Runtime, Queue, Cortex, Gateway, and Business refactors. These references can mislead future agents into using old paths or collapsing service boundaries.

## Proposed Solution

Audit the remaining semantic/app/device service residue across active docs/scripts/code, classify each class of hit as active, generated, historical, lower-level protocol, or stale. Patch safe active-surface stale claims directly. If a broad or risky cleanup cannot be closed safely, split it into child problems with exact scope and verification plans.

## Acceptance Criteria

- Active vs stale/generated/historical/lower-level references are classified with file evidence.
- Safe active-surface misleading claims are patched.
- Unsafe broad cleanup is split into follow-up child problems rather than silently accepted.
- Verification includes focused `rg` scans and relevant tests/lints for touched files.
- Final result records residual risks and explains why any remaining references are intentional.

## Verification Plan

Use targeted `rg` scans over docs, scripts, app resources, Device, Gateway, Business, Runtime, Queue, Cortex, Blob, LogicalFS, Sandboxd, and VMuse/VmControl surfaces. For any changed code, run the closest focused unit/contract tests. For docs-only patches, run scans proving the stale phrasing was removed or replaced with current boundary language.
