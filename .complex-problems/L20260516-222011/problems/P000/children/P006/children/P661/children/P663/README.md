# Architecture guard gap remediation

## Problem

Using the guard inventory, identify concrete missing or stale guard coverage for current contracts and add/update narrowly scoped guards only where justified.

## Success Criteria

- Compares current contracts against inventory.
- Patches missing/stale guards when a concrete gap exists.
- Avoids broad string bans that would break lower-layer generic tests/docs.
- Records any no-change decisions with evidence.
