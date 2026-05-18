# HD Screenshot Contract Comment Cleanup Result

## Summary

Updated the HD screenshot route comments so they no longer imply screenshots are sent directly to the LLM. The comments now describe the correct boundary: VmControl captures/compresses the raw screenshot, while agent-facing shell tooling stores it as a Blob artifact and uses the display contract for perception.

## Done

- Updated `novaic-app/src-tauri/vmcontrol/src/api/routes/hd_tools.rs`.
- Replaced “screenshots sent to LLM” wording.
- Clarified raw HD API versus agent-facing blob/display projection.
- Updated JPEG encoding comment to refer to compact artifact persistence.

## Verification

- Targeted stale phrase scan returned no matches:
  - `sent to LLM`
  - `direct.*LLM`
  - `LLM.*screenshot`
  - `base64.*LLM`
  - `screenshot.*LLM`
- Positive scan confirmed the new `Blob artifact` and `display contract` wording.
- `git diff --check -- src-tauri/vmcontrol/src/api/routes/hd_tools.rs` passed.
- `cargo fmt --check` for the crate and `rustfmt --edition 2021 --check` for the file were attempted; they fail on broad pre-existing formatting diffs outside this comment change, so they are not reliable closure signals for this ticket.

## Known Gaps

- `hd_tools.rs` still has pre-existing rustfmt diffs unrelated to this comment cleanup. This ticket intentionally avoided a broad rustfmt churn pass.

## Artifacts

- Modified `hd_tools.rs` comments only.
