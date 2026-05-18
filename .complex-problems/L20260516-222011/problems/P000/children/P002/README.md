# Shell tool contract and CLI usability audit

## Problem

Audit and optimize the current shell-first tool model: LLM-visible tool count, shell output truncation, `desc`, `agentctl`, `devicectl`, `cortex` CLI coverage, blob artifact contracts, and hidden direct-tool residue.

## Success Criteria

- Shell contract implementation and tests are inspected.
- CLI help/dispatch coverage is checked for current intended capabilities.
- Any direct-tool residue or misleading old paths are removed or made unreachable with tests.
- Targeted tests verify shell output and CLI contract behavior.
