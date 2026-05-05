# PR-221 Legacy / Compatibility Documentation And Script Drift Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Documentation and obsolete script cleanup |
| Created | 2026-05-05 |
| Scope | root docs and scripts |
| Dependencies | PR-218 |

## Goal

Remove misleading old-path documents and scripts that make the active system
look like it still has retired relay, Gateway-centric, VM, noVNC, or legacy
fallback branches.

## Small Tickets

### 1. Migration Script Review

- Objective: inspect old migration scripts and delete scripts for retired
  deployments.
- Scope: root `scripts/` and runbooks.
- Expected result: scripts retained only when they serve current operations.
- Verification: targeted `rg` and shell syntax check for retained scripts when
  practical.

### 2. Gateway / Entangled Historical Wording Cleanup

- Objective: update active docs so Gateway, Business, Entangled, and App
  ownership is not described through retired architecture.
- Scope: `docs/gateway`, `docs/entangled`, architecture docs.
- Expected result: historical text is moved to historical index or deleted when
  no longer useful.
- Verification: targeted doc scan.

### 3. noVNC / VM Historical Tail Cleanup

- Objective: remove noVNC or retired VM UI wording from active docs unless it
  clearly describes historical context.
- Scope: VMControl docs and frontend docs.
- Expected result: active docs describe current WebRTC/device path only.
- Verification: targeted `rg`.

## Acceptance

- Active docs no longer imply retired paths are available.
- Obsolete scripts are physically removed.
- Remaining historical docs are explicitly historical.

## Verification

- targeted `rg` for `legacy`, `compat`, `fallback`, `relay`, `noVNC`, and
  retired VM/Gateway wording under docs/scripts.

## Closure Notes

- Deleted the retired relay migration script.
- Updated active Gateway, VMControl, Blob, WebRTC, and architecture docs to
  describe the current boundaries.
- Kept historical material only where the document itself is explicitly an
  archive or guardrail.
