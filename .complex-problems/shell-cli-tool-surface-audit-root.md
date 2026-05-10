# Shell CLI Tool Surface Audit

## Problem

Audit whether every tool capability that should live inside shell is actually exposed as a shell CLI command, and whether any migrated capability still remains as an LLM-facing tool schema or Runtime direct executor.

The intended boundary is:

- Outside shell: `shell`, `display`, `skill_begin`, `skill_end`, `sleep`.
- Inside shell as CLI capabilities: IM operations, subagent spawn/communication, audio QA, payload inspection/interpretation, device operations, and runtime/cortex diagnostics that are interface-like rather than harness lifecycle primitives.

The audit must inspect code, schemas, Runtime executors, Cortex shell capability installation, prompt instructions, and tests. It should distinguish intentional internal backend APIs from old LLM/Runtime direct tool residue.

## Success Criteria

- Enumerate the expected shell CLI capability groups and concrete commands.
- Verify LLM-facing schemas expose only the intended outside-shell harness tools.
- Verify Runtime direct executors expose only the intended outside-shell harness tools.
- Verify each expected inside-shell capability has a CLI path in Cortex sandbox/runtime code.
- Verify prompts/instructions point agents toward shell CLI commands rather than old direct tools.
- Verify tests guard the boundary, or identify precise missing test coverage.
- Record any gaps as explicit follow-up work rather than hiding them.
