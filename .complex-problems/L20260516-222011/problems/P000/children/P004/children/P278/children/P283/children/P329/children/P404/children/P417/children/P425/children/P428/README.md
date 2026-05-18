# Problem: ContextEvent lifecycle residue sweep

## Problem

Even if targeted tests pass, old compatibility strings, fallback branches, or direct payload inlining may remain in nearby source files.

## Goal

Search the relevant Cortex lifecycle/projection/workspace/API surface for leftover compatibility or direct-inlining patterns.

## Success Criteria

- Relevant residue hits are classified as live, test-only, docs/artifact, or unrelated.
- No live unclassified ContextEvent lifecycle residue remains.
- Any live issue is fixed or split.
