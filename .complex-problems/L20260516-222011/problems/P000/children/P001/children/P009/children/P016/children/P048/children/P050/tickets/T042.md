# Ticket: audit and fix media CLI stdout contract

## Problem Definition

Media CLI commands must not emit raw image bytes or base64 fields in stdout. The active screenshot/media command path should emit concise terminal text plus a blob/artifact manifest.

## Proposed Solution

- Locate active `devicectl` screenshot/media CLI implementations and any wrapper paths exposed through shell.
- Search for raw base64 fields such as `screenshot`, `data`, `data:image`, or inline image JSON returned to stdout.
- Patch any active CLI path that still returns raw media bytes so it returns a manifest with blob URI, metadata, and concise text.
- Add or update focused tests around the media CLI contract.

## Acceptance Criteria

- Active screenshot/media CLI stdout contains artifact/blob metadata, not raw image bytes.
- Tests or scans verify that screenshot/media CLI output excludes raw base64 fields.
- Any remaining base64 fixtures are explicitly test-local and not part of active CLI stdout.

## Verification Plan

- Run focused `rg` scans for screenshot/base64 output fields.
- Run targeted tests covering device CLI or shell-wrapped screenshot output.
- If code changes are needed, rerun relevant unit/contract tests.

## Risks

- Some lower-level device API may still return base64 internally; that is acceptable only if the CLI projection converts it before stdout.
- Tests must distinguish internal API payloads from user-facing shell stdout.

## Assumptions

- `blob://runtime-artifact/...` is the intended carrier for screenshot bytes.
- The shell observation contract should see a compact manifest, not the original device API payload.
