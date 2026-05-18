# Ticket: Audit Cortex CLI and shell capability surface

## Goal

Verify shell-facing Cortex CLI/capabilities follow the current tool-output/blob/pointer contract and do not retain old raw-output compatibility paths.

## Acceptance Criteria

- CLI/capability inventory artifact saved.
- Shell capability tests pass.
- No live CLI path emits raw media/base64 or bypasses pointer payload inspection.
- Any gap is fixed or split.
