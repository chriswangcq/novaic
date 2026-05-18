# RW Scratch Layout Cleanup and Test Update Check

## Summary

Success. The parent result is supported by closed child work: production default layout was changed, Cortex fixtures were rewritten, the current subagent scratch behavior remains represented, and an aggregate scan/test guard confirms no Cortex code/test still treats root `/rw/scratch` as the default/canonical scratch path.

## Evidence

- R628 removed `/rw/scratch` from `Workspace.initialize()` and changed the direct initialization assertion to a negative guard.
- R632 records fixture rewrite across workspace/authority, runtime/tool, and path-abuse test categories with child checks C670, C671, and C672 succeeding.
- R633 records final scan classification: Cortex has only a negative `rw/scratch/.keep` assertion; current intended behavior is `/rw/subagents/{id}/scratch`; LogicalFS root scratch hits are lower-layer generic tests.
- Focused verification covered 2 + 22 + 14 + 47 child tests, then an 88-test Cortex aggregate run and 9 LogicalFS tests.

## Criteria Map

- Removes high-confidence legacy root `/rw/scratch` initialization/contract references: satisfied by R628 and final scan R633.
- Keeps generic `/rw` path behavior covered by neutral/current paths: satisfied by R632 children using `/rw/tmp` and preserving the original invariants.
- Preserves LogicalFS `RW_SCRATCH=/rw/subagents/{id}/scratch` behavior: satisfied by R633 classification of `novaic-cortex/novaic_cortex/logical_fs.py` and sandboxd wiring coverage.
- Runs focused Cortex and LogicalFS tests: satisfied by recorded child and aggregate runs.

## Execution Map

- Default layout cleanup executed in P638.
- Cortex fixture rewrites split and executed in P641, P642, and P643, rolled up by P639.
- Residue verification executed in P640.

## Stress Test

The strict post-scan is the right stress test for the likely failure mode: old paths remaining after piecemeal fixture migration. It covered both source and tests across Cortex/LogicalFS and classified all hits.

## Residual Risk

The only residual root scratch strings are outside Cortex semantics or are negative guards. No blocking follow-up is required for this parent problem.

## Result IDs

- R634
