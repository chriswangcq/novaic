# Audit Runtime and Cortex Multimodal Compatibility Residue

## Problem Definition

P618 must find runtime/Cortex display/shell/projection compatibility branches that might bypass BlobRef/display-perception contracts or replay historical media into normal LLM history.

## Proposed Solution

Scan runtime and Cortex code/tests for base64/data URI/image_url/image_ref/multimodal/display projection compatibility terms, classify reachable branches, and run focused runtime/Cortex projection/history tests.

## Acceptance Criteria

- Exact runtime/Cortex scan is recorded.
- Current display-perception and historical projection behavior are classified with line references.
- Focused projection/history tests pass.
- Risky reachable compatibility residue is removed or followed up.

## Verification Plan

Run `test_pr71_no_tool_retry_context_cleanup.py`, no historical image injection tests, Cortex tool/step projection tests, and shell blob contract tests.

## Risks

- `image_ref` support is intended for current display perception; do not remove that path.

## Assumptions

- Historical display replay must remain text/image_ref placeholder only, not resolved to provider image bytes.
