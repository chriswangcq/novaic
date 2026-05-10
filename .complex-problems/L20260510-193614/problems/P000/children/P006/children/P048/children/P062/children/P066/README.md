# Phase 5D.2b Step Formatting And Sandbox Contract Guard Coverage

## Problem

Review and, if needed, tighten guards for public step formatting and sandbox path contracts: public step formatting must use explicit `projection`, and temp sandbox backing paths must remain rejected.

This belongs under P062 because step formatting/sandbox contracts are independent from scope authority.

## Success Criteria

- Identify tests covering unsupported step projection and absence of public `include_display`.
- Identify tests covering stable `/cortex/ro` / `/cortex/rw` guidance and rejection of `novaic-cortex-sandbox-*` backing paths.
- Run the relevant tests or add missing guards.
- Classify low-level `include_display` resolver internals separately from public API.
