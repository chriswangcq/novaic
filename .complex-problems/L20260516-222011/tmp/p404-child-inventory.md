# Cortex residue inventory and live-surface map

## Problem

Before modifying Cortex code, we need a precise Cortex-only residue inventory that excludes virtualenv/generated/cache files and separates live runtime surfaces from historical docs or ledger artifacts.

## Success Criteria

- Run Cortex-specific guards for generation defaults, active-state lookup, archive diagnostics, and context event lifecycle residue.
- Save guard outputs under the ledger tmp directory.
- Classify files into live code, tests, migration/scripts, docs/history, and generated/cache exclusions.
- Produce a live-surface map that downstream Cortex cleanup children can consume.
- Create follow-up children if the inventory reveals a slice too broad for the current plan.

