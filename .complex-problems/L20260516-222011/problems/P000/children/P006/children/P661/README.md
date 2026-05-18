# Architecture Guard Coverage Audit

## Problem

Review existing CI/static guard scripts to ensure corrected contracts are protected, not just documented. Add or adjust targeted guards when a real gap is found.

## Success Criteria

- Inventories root CI guard scripts relevant to old paths, tool contracts, lifecycle, Blob/LogicalFS boundaries, and generated artifacts.
- Identifies missing or stale guard coverage for current contracts.
- Adds/updates guards only for concrete gaps.
- Runs changed guards and records outputs.
