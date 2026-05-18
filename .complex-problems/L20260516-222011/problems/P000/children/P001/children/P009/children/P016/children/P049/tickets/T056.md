# Ticket: update docs for terminal text plus blob/artifact output contract

## Problem Definition

Documentation and examples can lag behind the new tool-output contract, encouraging future agents or developers to serialize raw base64, reuse ephemeral paths, or treat shell output as a media transport.

## Proposed Solution

Scan active docs for shell/display/blob/artifact guidance and media/base64 examples. Update the main active documentation so it states the current contract: shell returns bounded terminal text, complete data lives in Cortex RO/durable payloads, media-producing CLI returns blob/artifact manifests, and `display` is the explicit image perception path.

## Acceptance Criteria

- Active docs describe terminal text plus artifact/blob manifests.
- Active docs warn against raw base64 in shell/tool text and against reusing ephemeral backing paths.
- Historical docs/examples with old behavior are classified or left untouched only if clearly not active guidance.
- Focused docs scan and verification are recorded.

## Verification Plan

Run targeted `rg` scans for `base64`, `data:image`, `display`, `artifact`, `blob`, `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, `/cortex/ro`, and shell contract wording in docs. Re-run relevant focused code tests if documentation edits touch examples referenced by tests.

## Risks

- Over-editing historical design notes can erase useful context. Prefer updating active runtime/tool-chain docs and explicitly classifying historical material.

## Assumptions

- Code behavior is already handled by P048; this ticket is documentation and examples only unless the docs scan reveals an active broken example embedded in tests.
