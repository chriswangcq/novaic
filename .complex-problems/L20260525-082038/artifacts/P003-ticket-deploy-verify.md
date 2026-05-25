# Deploy and verify message recovery

## Problem Definition

The Entangled fix must be shipped through the current Release Controller path and production must recover from the stuck Environment notification without using manual backend deploy scripts.

## Proposed Solution

Commit the Entangled fix, update the parent submodule pointer and ledger, push to GitHub, trigger Release Controller for staging, verify the immutable image release, then promote the same release to prod. After prod deploy, verify Entangled no longer emits duplicate `updated_at` errors, subscriber claims and dispatches pending notifications, Queue/Runtime consumes the message pipeline, and public health remains green.

## Acceptance Criteria

- Entangled fix and parent pointer/ledger are committed and pushed.
- Release Controller runs the deployment path, not direct manual `services-image`.
- Staging deploy succeeds for the commit/image.
- Prod is promoted through Release Controller or, if the controller's current API requires it, the same controller-managed release pointer is used.
- Production subscriber recovers from the stuck notification and no longer loops on Entangled 500.
- Queue/Runtime and public health checks are green after recovery.

## Verification Plan

Use Release Controller health/run APIs, container health, subscriber metrics/logs, Entangled logs, Queue diagnostic endpoints, and public health endpoints. If possible, trigger a minimal message-path smoke without exposing secrets or private message content.

## Risks

- Pending notifications may produce delayed Runtime work immediately after deploy.
- If Release Controller worktree lags submodule pointers, a worktree repair/update may be required before triggering.

## Assumptions

- The current API host Release Controller is the authoritative CD path at `127.0.0.1:19880`.
