# Ticket: Sweep ContextEvent lifecycle residue

## Goal

Search the relevant Cortex lifecycle/projection/workspace/API source surface for leftover compatibility, fallback, or direct inlining patterns that could bypass the cleaned ContextEvent contract.

## Acceptance Criteria

- Residue search covers Cortex source and tests for context events, projections, workspace payload/step handling, and API lifecycle endpoints.
- Hits are classified as live, test-only, docs/artifact, or unrelated.
- No live unclassified residue remains.
- Any live issue is fixed or split.
