# Final RW Scratch Residue Scan Classification

## Problem

The final guard needs a fresh scan that classifies every remaining root `/rw/scratch` occurrence after the cleanup chain, so stale production/default-contract residue cannot hide behind prior results.

## Success Criteria

- Runs and records fresh scans for `/rw/scratch`, `rw/scratch`, `RW_SCRATCH`, and `/rw/subagents` across Cortex and LogicalFS.
- Classifies every remaining root `/rw/scratch` hit as negative guard, lower-layer generic test, or follow-up-worthy residue.
- Confirms Cortex production code and positive test fixtures no longer advertise root `/rw/scratch` as default/canonical scratch.
