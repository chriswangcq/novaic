# Session direct side-effect bypass classification

## Problem

Search for direct side effects that may bypass durable session outbox ownership and classify or fix them.

## Success Criteria

- Search for direct saga creation/publish, attach input publish, archive/recovery publish, and wake-created active-state mutation paths.
- Classify each hit as safe implementation detail, risky bypass, or removable residue.
- Fix risky bypasses or split concrete follow-up children with tests.
- Save guard artifacts under `.complex-problems/L20260516-222011/tmp/p459/`.
