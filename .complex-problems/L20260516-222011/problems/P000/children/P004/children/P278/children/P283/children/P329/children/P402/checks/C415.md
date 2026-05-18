# Compatibility residue guard inventory check

## Summary

`P402` is successful as an inventory-only problem. It created guard outputs across runtime, Cortex, tests, and migration-like scopes, saved evidence files, and identified downstream cleanup buckets without modifying implementation code.

## Evidence

- `R389` records guard output files under `.complex-problems/L20260516-222011/tmp/p402-guards/`.
- The inventory includes narrow live-default, active lookup/mutation/archive, tests/fixtures compatibility, and migration-like searches.
- A corrected no-venv migration search found zero project migration-like files.
- Runtime/Cortex/test hit clusters are identified and delegated to `P403`, `P404`, and `P405`.

## Criteria Map

- Run source guards covering generation/session_generation/expected_generation/finalize_generation/current_generation defaulting, optional branches, active lookup, and active clear/restart/archive helpers: satisfied by `narrow-live-defaults.txt` and `active-lookup-mutation.txt`.
- Include runtime queue code, task handlers/sagas/contracts, Cortex code, tests, and migration-like directories: satisfied by the recorded scopes and migration search.
- Produce a hit matrix with file references and initial classification buckets: satisfied by `R389` guard counts and cluster summary.
- Identify which hits are already safe or require child cleanup: satisfied at the inventory level by delegation to `P403`-`P406`.
- Do not change implementation code in this inventory child: satisfied; only ledger tmp evidence files were written.

## Execution Map

- `T394` was classified one-go because it was read-only and bounded.
- Execution saved five guard output files and one no-venv corrected migration file.
- Result `R389` records the evidence and delegates unresolved classifications to sibling cleanup children.

## Stress Test

- The inventory ran both narrow and broad guards. The broad guard intentionally produced many false-positive candidates, which are retained for downstream classification rather than filtered away.
- The initial migration search included `.venv`; the execution corrected that with a no-venv project search before recording the result.

## Residual Risk

- Non-blocking for P402: the inventory does not classify every hit to finality. That is explicitly the job of P403-P406.

## Result IDs

- `R389`
