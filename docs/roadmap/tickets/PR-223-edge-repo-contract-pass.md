# PR-223 Edge Repo Contract Pass

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Edge repository contract tightening |
| Created | 2026-05-05 |
| Scope | `novaic-quic-service`, `novaic-mcp-vmuse`, other non-hot-path repos if relevant |
| Dependencies | explicit boundary contract cleanup |

## Goal

Apply the same explicit-input, no-hidden-fallback review to edge repositories so
they do not keep stale branches that can mislead future work even if they are not
on the hottest product path.

## Small Tickets

### 1. QUIC Service Scan

- Objective: scan `novaic-quic-service` for implicit inputs, fallback branches,
  and stale docs.
- Scope: Rust source, deploy config, docs if present.
- Expected result: either no changes needed or current contract is made explicit.
- Verification: cargo checks/tests where available and targeted residue scan.

### 2. MCP VMUse Scan

- Objective: scan `novaic-mcp-vmuse` for implicit inputs, fallback branches, and
  stale docs.
- Scope: source, package/config files, docs if present.
- Expected result: no misleading old branches remain.
- Verification: available build/tests and targeted residue scan.

### 3. Edge Repo Summary Guard

- Objective: document and, where practical, test the edge repo boundary.
- Scope: repo-local README/docs or tests.
- Expected result: future maintainers can tell what these repos own and what
  they must not own.
- Verification: source review and available tests.

## Acceptance

- Edge repos have been scanned with the same cleanup standard as hot-path repos.
- Any retained defensive behavior is named as current product behavior, not old
  fallback.
- Available repo checks pass.

## Verification

- `cd novaic-quic-service && cargo test` or `cargo check`
- `cd novaic-mcp-vmuse && npm test` / package-specific check if available.
- targeted `rg` for `fallback`, `compat`, `legacy`, and implicit config paths.

## Closure Notes

- `novaic-quic-service` now requires explicit `GATEWAY_URL` and no longer
  accepts the retired `LISTEN_PORT` alias.
- Removed the unused JWT-only auth helper from the QUIC relay.
- `novaic-mcp-vmuse` keeps MCP-local base64 image/file transport, but removed
  stale qemudebug/legacy/fallback/compat wording and added a guard test for
  those retired markers.
