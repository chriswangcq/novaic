# Add release-controller branch head polling

## Problem

The release-controller core service needs a polling component that reads configured branch rules, checks branch heads, records changed heads, skips unchanged heads, and triggers the existing planner/runner path for eligible non-prod branch releases.

## Success Criteria

- A poller module can list configured branch patterns and resolve concrete branch heads from git.
- Branch head state is persisted in `branch-heads.json`.
- Unchanged branch heads are skipped without creating duplicate release runs.
- Changed `main` and `preview/*` heads can create release plans through the existing planner.
- `release/*` heads can create candidate-only plans through the existing planner.
- Poll-triggered execution cannot target prod.
- Unit tests cover changed head, unchanged head, and unmatched branch behavior without network access.
