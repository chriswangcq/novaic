# Verify Device/artifact/display boundary after remediation

## Summary

Run a focused post-remediation verification sweep across code scans and tests to prove no active large-media-as-text path remains.

## Problem Definition

Screenshot/display paths are high-risk. After remediation, we need evidence that shell output, context projection, display perception, Device routes, and docs/tests still match the intended media boundary.

## Proposed Solution

Split verification into scan classification and focused test execution, then summarize the final state.

## Acceptance Criteria

- Code/document scans cover screenshot, base64, Blob URI, display projection, shell output, and `tool-output.v1` terms.
- Focused tests for shell contract, projection/history, display multimodal, Device route, and resource hygiene pass or record blockers.
- Remaining hits are classified as current contract, test guard, historical note, lower-level protocol, or follow-up.
- No active unexamined large-media text leak remains in swept surfaces.

## Verification Plan

- Run targeted `rg` sweeps.
- Run the focused pytest groups already identified by discovery and remediation.
- Record any residual risk explicitly.
