# App resource and generated asset semantic residue discovery ticket

## Problem Definition

`novaic-app` resource copies and generated assets may preserve stale tool/media/session/file-boundary behavior after source services change. Discovery must distinguish source-of-truth code from synchronized copies and third-party bundled resources.

## Proposed Solution

Split discovery by app asset family: VMuse copied resources already identified under service-code discovery, broader app resource/generated surfaces need focused scanning for display/shell/device/session/file-boundary residue without manually patching generated assets during discovery.

## Acceptance Criteria

- Relevant app resource/generated asset locations are identified.
- Findings distinguish synchronized generated/resource copies from source-of-truth source code and docs.
- Required sync/remediation candidates are listed.
- No generated assets are manually patched in this discovery child.

## Verification Plan

Use bounded `rg --files` and focused `rg` scans under `novaic-app/src-tauri/resources`, `novaic-app/src-tauri/gen`, and selected `novaic-app/src`/`src-tauri` app code surfaces for VMuse, Device, display, shell, Blob, LogicalFS, sandbox, base64, and direct-media residue. Split if independent asset families need separate checks.

## Risks

- App resource trees contain large third-party Android/QEMU assets; broad scans must filter those rather than treating third-party vocabulary as NovaIC residue.
- Generated copies should generally be regenerated or synchronized from source, not manually edited as the long-term source of truth.

## Assumptions

- VMuse copied resource cleanup has already been identified under P766, but P754 may add broader app-level sync or generated-asset findings.
