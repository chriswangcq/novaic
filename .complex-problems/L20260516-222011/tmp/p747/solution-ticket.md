# Run post-remediation media-boundary scan

## Summary

Run targeted scans for media-boundary terms and classify remaining hits after remediation.

## Problem Definition

After code/doc cleanup, we need a skeptical scan to ensure no active shell/history/display route still leaks large media bytes as text.

## Proposed Solution

Run focused `rg` commands over high-risk packages and inspect residual hits enough to classify them.

## Acceptance Criteria

- Scans cover Device, Cortex, Runtime, VMuse, app, docs, and scripts.
- Removed Device screenshot route is absent.
- Remaining hits are classified.
- Any active unclassified leak becomes a follow-up/blocker.

## Verification Plan

- Run route-specific scan.
- Run broader media-term scan.
- Inspect representative residual hits and record classification.
