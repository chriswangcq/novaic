# Active code fallback and compatibility residue scan

## Problem

Active implementation code may still contain stale fallback, compatibility, legacy, or migration branches that preserve old behavior after the newer queue/FSM/shell/display/blob contracts were introduced.

## Success Criteria

- Focused scans cover active implementation directories while excluding ledger/build/cache noise.
- Hits are classified as active risk, intentional guard, benign adapter, or historical residue.
- Tiny high-confidence cleanup is applied directly if safe.
- Larger active-risk branches are routed to follow-up or spawned child problems instead of being summarized away.
