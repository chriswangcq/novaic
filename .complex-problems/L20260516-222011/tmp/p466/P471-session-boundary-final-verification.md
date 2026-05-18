# Session explicit-boundary final verification

## Problem

After inventory and remediation children close, run a final verification pass proving the session/worker hidden-input and duplicate-config audit is complete.

## Success Criteria

- Re-run hidden-input, duplicate-config, and residue guards and save artifacts.
- Run focused pytest suites covering session repository, outbox, FSM, runtime handler generation checks, and relevant subscriber/dispatcher setup.
- Map each P466 success criterion to evidence.
- Record residual risk explicitly; do not mark success if a risky hidden input remains.
