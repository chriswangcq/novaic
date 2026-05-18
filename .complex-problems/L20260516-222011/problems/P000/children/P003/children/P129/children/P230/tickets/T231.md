# Audit tool guidance and payload boundary tests

## Problem Definition

Tool schemas, shell capability guidance, and tests must consistently teach the new boundary: shell returns bounded terminal text; full payload inspection requires explicit payload tools/CLI; display/media image data must not be treated as ordinary text history.

## Proposed Solution

Inspect tool surface policy, generated/direct tool schemas, shell capability help, payload CLI guidance, and existing boundary tests. Fix any misleading guidance or stale test naming found during audit, then run focused schema/guidance tests.

## Acceptance Criteria

- Tool schema/policy exposure for payload tools is mapped and consistent with explicit payload inspection.
- Shell capability guidance describes bounded terminal output and explicit payload commands without encouraging raw payload/base64 in context.
- Focused tests for tool schemas, shell capabilities, and payload/output boundary pass.
- Any stale/misleading guidance found is cleaned up rather than documented as acceptable residue.

## Verification Plan

Use `rg` and line-numbered inspection over `tool_surface_policy.py`, `shell_capabilities.py`, tool schema tests, and output contract tests. Run focused tests for tool schemas, shell capabilities, output contracts, and payload API boundaries.

## Risks

- Guidance may be spread across generated docs or historical tests; distinguish active surfaced guidance from archival ledger content.

## Assumptions

- Runtime/write/context behavior is already audited in `P228` and `P229`; this ticket focuses on exposed contracts and test coverage.
