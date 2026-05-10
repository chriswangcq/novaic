# Phase 5B3 Compatibility Wrapper Review And Removal

## Problem

P045 found live compatibility/legacy wording in source and tests. Some are guard tests, but wrappers such as `step_result_projection.py` compatibility functions may be stale. We need to remove wrappers that only preserve old APIs and keep only explicitly justified current adapters.

## Success Criteria

- Review source/test hits for `compat`, `compatibility`, `legacy`, and `fallback`.
- Delete or rename wrappers that are not part of the current public contract.
- Keep guard tests that prove legacy paths are removed.
- Any remaining compatibility/migration code has a current justification, such as schema migration or public adapter behavior.
- Targeted tests for tool output projection and context event no-compat behavior pass.
