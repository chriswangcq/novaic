# MCP Test Residue Scan

## Problem

MCP package tests may contain stale compatibility, fallback, migration, skip, or base64 fixture residue around tool contracts.

## Success Criteria

- Scan MCP package tests for residue markers.
- Classify hits as current guard tests, fixture text, or stale residue.
- Remove safe stale wording or fixtures if found.
- Run focused MCP tests or record explicit no-code-change verification.
