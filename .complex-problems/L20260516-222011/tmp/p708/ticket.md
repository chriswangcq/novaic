# Device/devicectl and artifact-display boundary classification ticket

## Problem Definition

Device/devicectl, display, Blob/artifact storage, and LLM context projection have been actively refactored. The project needs a boundary audit that confirms device capture/control stays in Device/devicectl, large media bytes are externalized through Blob/artifact manifests, display projects media correctly to the model, and stale docs/code claims are patched or recorded.

## Proposed Solution

Split this problem into discovery, safe remediation, and final verification. First map Device service/devicectl entrypoints, launch paths, CLI output contracts, and display/artifact projection surfaces. Then patch active stale claims or contract violations if safe. Finally run focused scans/tests/lints that prove screenshots/artifacts do not leak large base64 into shell/context paths and that remaining references are intentional.

## Acceptance Criteria

- Device/devicectl entrypoints and launch references are inventoried.
- Boundaries are explicit: Device controls hardware, devicectl is shell-facing CLI, Blob stores bytes, display projects media, Cortex/Runtime context stores references/manifests.
- Active stale docs/code claims or small contract violations are patched.
- Large screenshot/artifact output behavior is verified as blob/manifest-only where relevant.
- Final scans/tests/lints classify residual hits and identify follow-ups if needed.

## Verification Plan

Use focused `rg` scans over `novaic-device`, `novaic-agent-runtime`, `novaic-cortex`, `novaic-mcp-vmuse`, `docs`, and launch scripts. Run relevant existing CI/lint/test commands for blob workspace boundary, device/tool output contract, context projection, or compile checks depending on findings.

## Risks

- Device/display/blob spans multiple repos and may require further sub-splitting.
- Some historical roadmap docs intentionally contain old base64/display behavior and should not be patched as active code.
- End-to-end device tests may require live host-device services; use static/contract tests if live hardware is unavailable.

## Assumptions

- The active target contract is shell text plus blob/artifact manifest, with display responsible for model-visible media projection.
- This audit should not redeploy services unless a later explicit deployment ticket is created.
