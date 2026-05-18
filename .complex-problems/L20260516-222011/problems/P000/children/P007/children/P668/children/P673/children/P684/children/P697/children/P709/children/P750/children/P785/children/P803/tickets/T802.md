# Update HD Screenshot Contract Comments

## Problem Definition

`hd_tools.rs` still says HD screenshots are sized for screenshots "sent to LLM", which conflicts with the current contract where the raw HD API may produce image bytes/base64 for internal transport, while agent-facing shell CLI stores screenshots as blob artifacts and uses `display` for visual perception.

## Proposed Solution

Patch comments in the HD screenshot route to describe the current boundary: capture/compress in VmControl, then higher-level tooling stores/presents via blob/display. Do not change runtime behavior unless comment scan exposes a direct LLM injection path.

## Acceptance Criteria

- No relevant HD screenshot comment says images are sent directly to the LLM.
- Comments clarify the raw API versus agent-facing blob/display projection boundary.
- Targeted scan for stale phrases passes.
- Rust formatting/check or a targeted syntax-level check runs if feasible.

## Verification Plan

- Patch comments in `novaic-app/src-tauri/vmcontrol/src/api/routes/hd_tools.rs`.
- Run targeted `rg` for `sent to LLM`, `LLM`, `base64`, `blob`, `display`, and `screenshot` in relevant route code.
- Run `cargo fmt --check` for `src-tauri/vmcontrol` if available/fast enough.

## Risks

- The raw route still returns base64 internally; the ticket is about stale comments, not changing the API payload.

## Assumptions

- The agent-facing CLI/display contract is the correct place to convert screenshot payloads into blob artifacts.
