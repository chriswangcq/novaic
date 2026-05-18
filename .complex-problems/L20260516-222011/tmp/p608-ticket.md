# Ticket: Audit Frontend Artifact and Image Rendering

## Problem Definition

Frontend artifact/image surfaces should present BlobRef-backed images/files through artifact-specific UI or safe textual placeholders, not by embedding raw base64 or data URLs in normal Agent Monitor/timeline text.

## Proposed Solution

Scan `novaic-app` and relevant factory/static UI for BlobRef, artifact, thumbnail, image, base64, data URL, attachment, and display rendering paths. Capture exact slices and run focused tests that cover BlobRef/file attachment behavior and ActivityTimeline payload redaction. Record whether Agent Monitor currently has artifact-specific rendering or intentionally uses text-only placeholders.

## Acceptance Criteria

- Exact scans for artifact, BlobRef, thumbnail, image, base64, and data URL rendering paths are recorded.
- Slices show artifact-specific rendering or clear text-only fallback behavior.
- The result explains how UI artifact display differs from LLM display-perception image injection.
- A follow-up is created if normal UI paths render image artifacts as raw base64 text.

## Verification Plan

Use source scans and focused tests for blob attachment path, ActivityTimeline redaction, and factory redaction. If no Agent Monitor artifact UI exists, record that as text-only behavior rather than inventing a feature.

## Risks

- Chat attachment rendering and Agent Monitor artifact rendering are different surfaces; do not conflate them.
- Some base64 occurrences are legitimate local media fixtures or native WebRTC/clipboard internals.

## Assumptions

- Blob Service remains the place for binary file transport; UI should consume BlobRef/image URLs or safe placeholders.
