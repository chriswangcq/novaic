# PR-231 — VNC / noVNC Boundary Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | App VM display boundary cleanup |
| Created | 2026-05-05 |
| Scope | App frontend, Tauri vmcontrol display routes, docs/comments |
| Dependencies | PR-195, PR-225 |

## Goal

Keep the RFB/VNC pieces that are required as VM capture/control internals, but
remove browser noVNC product-route residue and misleading wording.

## Small Tickets

### PR-231A — Identify Live Product Boundary

- Objective: classify VNC/RFB usage as either WebRTC capture internals,
  user-session management, or obsolete direct noVNC route.
- Scope: App TS/TSX, vmcontrol routes/modules, setup/log wording.
- Expected result: a concrete delete/rename list.
- Verification: source review and targeted grep.

### PR-231B — Remove or Rename Direct noVNC Route Surface

- Objective: delete direct noVNC websocket/browser-route surfaces if unused; if
  a route is still required internally, rename comments/logs to RFB/VNC internal
  transport instead of browser noVNC.
- Scope: vmcontrol VNC route/module registration and comments.
- Expected result: no active product code advertises browser noVNC as a current
  UI path.
- Verification: cargo check and targeted grep.

### PR-231C — App Wording Cleanup

- Objective: align App comments/local product labels with current WebRTC display
  path while preserving necessary “restart VNC” user-session actions if they are
  still real.
- Scope: App TS comments/locale keys if needed.
- Expected result: no stale noVNC wording in active frontend.
- Verification: App unit/type checks and targeted grep.

## Acceptance

- Browser noVNC is not presented as an active user-facing route.
- Required RFB/VNC internals remain functional and clearly named as internals.
- `cargo check` for vmcontrol passes.

## Closure

Closed 2026-05-05. The direct `/api/vms/:id/vnc` WebSocket route and `VncProxy`
module were removed. VM RFB remains only as an internal WebRTC capture/control
dependency via `vnc_endpoint.rs` and VM user-session management.
