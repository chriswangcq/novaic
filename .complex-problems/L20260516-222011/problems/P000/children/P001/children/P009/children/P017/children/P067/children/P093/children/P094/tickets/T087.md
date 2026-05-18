# MCP Test Residue Scan Ticket

## Problem Definition

MCP package tests may still contain stale compatibility/fallback/migration/base64 markers around final tool-output contracts.

## Proposed Solution

Scan MCP test files, classify each hit, clean safe stale wording, and run the MCP tests affected or representative.

## Acceptance Criteria

- MCP tests scanned for the residue marker set.
- Hits classified.
- Safe stale residue removed.
- Focused MCP verification recorded.

## Verification Plan

- `rg` scans over MCP test files.
- Run focused pytest for affected MCP packages.
