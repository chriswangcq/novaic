# Cortex Projection Contract Inspection Ticket

## Problem Definition

Inspect Cortex step result projection behavior and tests to determine how inline MCP media, data URLs, BlobRefs, and display outputs currently reach LLM context.

## Proposed Solution

Read `novaic-cortex/novaic_cortex/step_result_projection.py`, search Cortex tests for projection coverage, and record exact unsafe and safe paths. Do not patch code in this ticket.

## Acceptance Criteria

- Exact functions handling `_mcp_content`, image/data URL, and BlobRef-like structures are identified.
- Existing tests or missing tests are identified.
- The next patch child has a clear, bounded patch plan.
- No product files are modified.

## Verification Plan

Use `rg`, `sed`, and test file discovery. Record evidence pointers and patch recommendations.
