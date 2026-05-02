# Cortex Boundary Contract

Cortex has two core jobs:

1. Maintain the LIFO scope tree.
2. Assemble LLM context from that tree.

Everything else must either live in the owning service/package or be treated as an explicit legacy proxy surface with a narrow reason.

## Retired From Cortex

The following concepts must not re-enter active Cortex source:

- automatic summary generation
- user profile ownership or profile inference
- business memory/notebook/search proxying
- business task system ownership
- `wake summary`
- deriving durable memory from `im_reply` or raw chat text
- multiple parallel summary producers

The only durable LLM-authored summary path is:

`skill_end(report=...)` closes the current LIFO stack top (the wake scope or an LLM-opened child skill scope) and writes that scope's `summary.md` verbatim.

## Guardrail

`novaic-cortex/scripts/check_cortex_boundary.py` scans active Cortex Python source and fails on retired concepts. Parent CI runs it through `scripts/ci/lint_cortex_boundary.sh`.

Docs, tickets, and tombstones may mention retired concepts for archaeology. Active-code exceptions must be narrow, cite the owning PR, and be added to the guard's explicit allowlist rather than weakening the rule.
