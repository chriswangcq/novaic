# Runtime Legacy Execution Residue Classification

## Problem

Classify runtime production/test hits for direct subprocess/local/fallback/host/mount execution terms that may indicate legacy shell execution or stale compatibility branches.

## Success Criteria

- Records exact scans for subprocess/process/local/fallback/legacy/compat/host/mount terms in `novaic-agent-runtime`.
- Cites representative risky-looking production/test slices.
- Classifies hits as intended orchestration, test fixture, risky active bypass, or removable residue.
- Creates a follow-up if risky active runtime bypass remains.
