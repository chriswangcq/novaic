# Child Problem: common contract test fixtures

## Problem

Common contract tests use direct-tool names as generic fixtures in places that should describe current shell-first or final harness behavior.

## Success Criteria

- Generic current-contract fixtures use `shell` or another final harness tool.
- Direct-tool names remain only in explicit negative/guard assertions.
- Focused common tests pass.
