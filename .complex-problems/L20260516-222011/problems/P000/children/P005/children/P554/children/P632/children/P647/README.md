# Sandbox Backing Path Residue Audit

## Problem

Stable shell/filesystem contracts must not expose or depend on ephemeral `novaic-cortex-sandbox-*` backing paths. Remaining references need classification and cleanup if they define user/agent-facing behavior.

## Success Criteria

- Scans for `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW` where needed.
- Classifies hits as stable contract, defensive diagnostic, test fixture, historical artifact, or active ephemeral-path leak.
- Removes or creates follow-up for active ephemeral-path leak paths.
