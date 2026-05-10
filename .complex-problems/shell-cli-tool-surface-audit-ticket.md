# Audit shell CLI capability cutover

## Problem Definition

The architecture now intends most interface tools to live inside shell as CLI commands. The risk is that some old tool surfaces may still exist as LLM schemas, Runtime direct executors, prompt instructions, or unguarded compatibility branches, while some intended shell capabilities may be missing from the actual sandbox CLI implementation.

## Proposed Solution

Perform a bounded read-only audit across the relevant repositories:

1. Enumerate canonical outside-shell harness tools from common/cortex schemas.
2. Enumerate Runtime direct executors.
3. Enumerate Cortex sandbox CLI command families and subcommands.
4. Enumerate prompt/instruction references that teach agents how to use tools.
5. Search for migrated direct tool residue.
6. Review tests that enforce the boundary.
7. Produce an evidence-mapped result and call out precise gaps if any.

## Acceptance Criteria

- The audit states the expected shell CLI groups and concrete commands.
- The audit states the exact LLM-facing tool set.
- The audit states the exact Runtime executor set.
- The audit maps expected shell capabilities to implementation evidence.
- The audit identifies whether prompts point to CLI commands or old direct tools.
- The audit identifies whether tests guard the boundary.
- Any gap is specific enough to become a follow-up problem.

## Verification Plan

Use repository-local shell commands only:

- Python inventory checks for schema and executor sets.
- `rg` searches for old direct tool symbols.
- Source reads of `novaic_cortex/sandbox.py`, common schema files, Runtime tool handlers, prompt defaults, and tests.
- Targeted test runs where useful and cheap.

## Risks

- Some internal backend APIs share names with old tools; the audit must not misclassify backend APIs used by shell CLIs as LLM/Runtime direct residue.
- The repository is already dirty with prior work; do not revert unrelated changes.

## Assumptions

- `display`, `skill_begin`, `skill_end`, and `sleep` intentionally remain outside shell.
- `shell` is the only general-purpose entry point for migrated interface capabilities.
- Internal HTTP endpoints may remain if they are only used by shell CLI adapters.
