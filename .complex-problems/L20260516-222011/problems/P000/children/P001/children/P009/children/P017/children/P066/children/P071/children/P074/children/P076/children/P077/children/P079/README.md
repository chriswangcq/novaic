# Classify and clean Business entity/health stub wording

## Problem
`business/entity_store.py` and `business/internal/health.py` still contain `stub` wording. These may be harmless current minimal adapters, but the wording can mislead future AI/code readers into preserving old compatibility residue.

## Success Criteria
- Entity and health code are inspected for active behavior.
- Misleading `stub` wording is removed or replaced with precise current-state wording.
- Dead code is deleted if the path is no longer used.
