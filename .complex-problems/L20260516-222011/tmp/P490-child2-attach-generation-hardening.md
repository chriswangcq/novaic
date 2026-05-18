# Attach generation contract hardening

## Problem

If the inventory finds missing guard coverage or stale no-generation behavior, tighten the attach code/tests so active input delivery is generation-checked end to end. This belongs under P490 because attach must not deliver user input to the wrong wake.

## Success Criteria

- Missing no-generation/stale-generation behavior is removed or converted to strict validation/buffering.
- Focused tests cover the hardened boundary.
- Existing attach-race buffering behavior remains intact.
