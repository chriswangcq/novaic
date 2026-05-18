# MCP scripts and CI test residue scan

## Problem

MCP tests and repository scripts/CI tests may contain stale skip/TODO/FIXME/compat/fallback/legacy fixtures or policy comments that need classification.

## Success Criteria

- Scan MCP tests and scripts/CI test files for residue markers.
- Classify hits as intentional guard/policy vocabulary, harmless fixture text, or stale residue.
- Clean tiny stale residue when safe.
- Run focused MCP/script tests or explicit no-code-change verification.
