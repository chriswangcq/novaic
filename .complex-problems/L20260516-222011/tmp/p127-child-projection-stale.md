# Step result projection stale branch cleanup

## Problem

Projection code can accumulate legacy shapes and compatibility branches. Audit for old nested result wrappers, legacy content arrays, duplicate media converters, and stale projection branches that are no longer needed.

## Success Criteria

- Inventory projection-related production/test branches and legacy-shape tests.
- Classify each suspicious branch as active, test-only, compatibility, or stale.
- Remove stale code if safe.
- Run focused projection tests after cleanup or classification.
