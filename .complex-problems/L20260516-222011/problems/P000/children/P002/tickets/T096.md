# Shell Tool Contract and CLI Usability Audit Ticket

## Problem Definition

Audit and optimize the shell-first tool model: shell output truncation, `desc`, `agentctl`, `devicectl`, `cortex` CLI coverage, blob artifact contracts, and direct-tool residue.

## Proposed Solution

Inspect implementation/tests, exercise CLI help/contract paths, remove misleading residue or gaps, and run targeted shell/CLI contract tests.

## Acceptance Criteria

- Shell contract implementation and tests inspected.
- CLI help/dispatch coverage checked.
- Direct-tool residue or misleading old paths fixed or guarded.
- Targeted shell/CLI tests pass.

## Verification Plan

- Focused code/test scans.
- CLI help/smoke commands where safe.
- Focused pytest for shell output/CLI contract behavior.
