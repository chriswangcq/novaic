# Runtime Cortex Business Device Source Residue Patch Ticket

## Problem Definition

Patch precise source-level stale wording and compatibility residue across Runtime, Cortex, Business, and Device without broad refactors.

## Proposed Solution

Split by risk:

- Runtime/Business/Device wording cleanup: docstrings/comments that do not affect behavior.
- Cortex display/media projection compatibility cleanup: `step_result_projection.py` may affect active display/tool result behavior and needs focused tests.
- Device entity wording inspection: only patch if active/misleading after reading the exact context.

## Acceptance Criteria

- Runtime Cortex bridge docstring no longer overstates Cortex as the single gateway to agent storage.
- Business cancellation wording no longer implies direct Queue bypass.
- Device stale CASCADE cleanup comment is corrected or removed.
- Device entity wording is inspected and patched only if misleading.
- Cortex step result projection no longer preserves direct inline image/data URL compatibility if final contract is BlobRef-only.
- Focused tests or import checks pass for touched code.

## Verification Plan

Read exact files and split into low-risk wording changes versus Cortex behavior changes. For each child, patch minimally, run focused tests/imports, and run targeted `rg` checks for the stale phrases.
