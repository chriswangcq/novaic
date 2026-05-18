# Ticket: Display Tool Perception Contract Inventory

## Summary

Audit the display tool boundary end to end and classify whether media is exposed only through the intended current-turn perception path, while durable tool history and normal tool receipts remain bounded text.

## Problem Definition

Display is the primary media perception tool. Recent regressions showed screenshot bytes could appear as raw/base64 text in LLM request history. We need a focused inventory of display implementation, display result adapters, durable step history, and tests to determine whether this boundary is now clean or whether remediation must be forwarded.

## Proposed Solution

Run read-only scans over runtime, Cortex, tool configuration, blob/artifact, and test paths for display/media/base64/image handling. Read the relevant code slices, classify all hit buckets, and record whether display output is current-turn perception only, bounded textual history, removable compatibility, or risky residue.

## Acceptance Criteria

- Exact scan commands and output artifact paths are recorded.
- Relevant code/test slices are read with line references.
- Each hit bucket is classified as intended, risky, removable compatibility, or follow-up.
- Any high-confidence risky residue is explicitly forwarded to P554.

## Verification Plan

Because this is an inventory ticket, verification is the strict success check against the recorded scan artifacts and cited line references. Focused test execution belongs to the later aggregate verification ticket unless this inventory discovers a concrete risky code path.

## Scope

- Locate display tool implementation/configuration paths.
- Locate runtime adapters that classify display results as current perception or history.
- Locate Cortex/step-result formatting paths used by display.
- Locate tests that prove display media is split into provider image content and durable history is text-only.
- Identify any raw base64, compatibility fallback, or history replay path that should be forwarded to P554.

## Success Criteria

- Exact scan commands and output artifact paths are recorded.
- Relevant code/test slices are read with line references.
- Each hit bucket is classified as intended, risky, removable compatibility, or follow-up.
- Any high-confidence risky residue is explicitly forwarded to P554.
