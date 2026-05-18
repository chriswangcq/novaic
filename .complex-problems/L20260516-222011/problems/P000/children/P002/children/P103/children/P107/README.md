# Cortex CLI Coverage and Workspace Access Audit

## Problem

Cortex payload and workspace access must be usable from shell through stable CLI commands and stable `/cortex/ro`/`/cortex/rw` paths, without requiring agents to depend on ephemeral backing paths or direct non-shell tools.

## Success Criteria

- Locate Cortex CLI implementation and shell capability documentation for payload read/search/summarize/qa and workspace access.
- Verify stable path guidance is present and old ephemeral-path usage is blocked or discouraged.
- Run focused tests for Cortex payload/workspace shell contract if present.
- Fix missing or misleading Cortex CLI coverage if bounded.
