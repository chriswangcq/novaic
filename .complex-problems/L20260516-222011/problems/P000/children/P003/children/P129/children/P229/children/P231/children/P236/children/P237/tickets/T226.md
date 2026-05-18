# Verify runtime shell handoff projection boundary

## Problem Definition

Runtime shell execution must return compact terminal-style text to the LLM and keep raw/heavy stdout behind durable payload/artifact mechanisms. Shell should not inline huge stdout/base64 in normal tool history.

## Proposed Solution

Inspect shell tool handler/result projection code and tests. Verify public content truncation/manifest behavior and durable payload metadata. Run focused runtime shell projection tests.

## Acceptance Criteria

- Shell handler/projection files and functions are mapped.
- Code evidence shows bounded public shell result text and raw payload/artifact separation.
- Focused tests pass for shell output truncation, artifact manifest behavior, and no oversized history injection.

## Verification Plan

Use `rg`/`nl` over `novaic-agent-runtime` shell/tool handler code and run focused pytest files for shell projection and runtime context/media boundaries.

## Risks

- Some shell behavior may live in CLI packages outside runtime; this ticket audits runtime handoff, not every CLI command implementation.

## Assumptions

- CLI-specific output contract coverage is handled later by `P230`.
