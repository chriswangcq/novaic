# Attach generation final verification

## Problem

After inventory and any hardening, run final guards/tests to prove attach generation cleanup is closed. This belongs under P490 because no-generation compatibility residue tends to hide in tests or adapter code.

## Success Criteria

- Final guard artifact classifies remaining attach/generation hits.
- Focused attach/session tests pass together.
- Any remaining compatibility-looking hit is either guarded or routed to a follow-up.
