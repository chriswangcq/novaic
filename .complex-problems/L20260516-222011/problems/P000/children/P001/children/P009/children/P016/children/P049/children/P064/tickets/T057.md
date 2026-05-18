# Ticket: scan active docs for output-contract drift

## Problem Definition

Docs may still mention raw base64, ephemeral Cortex backing paths, or vague shell/display behavior. We need a scan/classification before editing active guidance.

## Proposed Solution

Run targeted `rg` scans over `docs`, service READMEs, and package docs for output contract terms. Classify findings into active docs to update, historical notes to leave alone, and test-only examples.

## Acceptance Criteria

- Active docs mentioning shell/display/blob/artifact/base64/ephemeral paths are identified.
- Files needing updates are listed explicitly.
- Historical docs/examples are classified so they are not silently treated as active guidance.

## Verification Plan

Use `rg` and minimal file reads. No code changes expected.

## Risks

- `docs/` contains architecture history; the result should not overstate historical notes as active product docs.

## Assumptions

- The sibling P065 will update active docs based on this scan.
