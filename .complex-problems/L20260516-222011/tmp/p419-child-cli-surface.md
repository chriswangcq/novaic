# Problem: Cortex CLI and shell capability cleanup

## Problem

Shell-facing CLI/capabilities can bypass the cleaned API contracts or emit large/raw payloads if old branches remain.

## Goal

Inventory and verify shell capabilities and CLI entry points.

## Success Criteria

- CLI/capability surface inventory saved.
- Tool output/blob contract tests pass.
- No live CLI residue remains unclassified.
