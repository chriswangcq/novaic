# Ticket: Display Tool Implementation And Blob Artifact Contract Inventory

## Summary

Inventory display tool implementation and configuration to verify direct display results are concise and media is loaded through stable artifact/blob references rather than raw base64 text.

## Problem Definition

Display is the explicit perception tool for images/media. If the display handler returns base64 or a giant JSON payload as text, the LLM request and durable history can bloat or mis-handle media. We need to audit the implementation/configuration side of display, not just downstream runtime projection.

## Proposed Solution

Run read-only scans for display tool definitions, display handlers, BlobRef loading, artifact handling, and image/base64 result formatting. Read relevant slices and classify each path as intended, risky, removable compatibility, or follow-up.

## Acceptance Criteria

- Exact scan commands and output artifacts are recorded.
- Display implementation/configuration slices are cited with line references.
- Direct display result shape is classified.
- Any raw media/base64 text path is forwarded to P554.

## Verification Plan

Inventory verification through strict success check over scan artifacts and cited slices. If a risky implementation path is found, create a remediation follow-up rather than marking success.
