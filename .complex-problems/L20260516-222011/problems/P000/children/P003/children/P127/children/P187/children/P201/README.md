# Projection stale branch regression sweep

## Problem

After production and test cleanup, we need a final aggressive sweep to ensure stale projection branches are not still connected or silently shadowing the new contracts.

## Success Criteria

- Re-run targeted `rg` audits over projection keywords and confirm no unclassified suspicious branches remain.
- Run the full focused projection/multimodal/factory-log test chain.
- Summarize residual risks and explicitly state whether any remaining compatibility branch is intentional.
