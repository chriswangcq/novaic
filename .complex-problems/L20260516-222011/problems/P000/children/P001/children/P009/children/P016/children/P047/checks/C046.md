# Check: Ephemeral Cortex Backing Path Residue

## Summary

Success. Result `R036` satisfies `P047`: the scan found no active instruction path that tells agents to reuse ephemeral `/tmp/novaic-cortex-sandbox-*` backing paths, and the remaining references are classified as prohibitions, guard tests, or historical/design context.

## Evidence

- Problem criteria require no active backing-path reuse guidance, clear classification of any remaining references, and a focused scan/classification record.
- Result `R036` records a focused scan for stable `/cortex/ro`, `/cortex/rw`, `$RO`, `$RW`, and ephemeral `novaic-cortex-sandbox-*` references.
- Result `R036` classifies each remaining ephemeral marker:
  - shell tool guidance warns against copying/reusing backing paths,
  - Cortex sandbox guard rejects direct backing-path usage,
  - tests cover the guard/schema wording,
  - docs retain historical/design context rather than current execution guidance.

## Criteria Map

- Active docs/prompts/tests do not instruct agents to reuse ephemeral backing paths: satisfied by `R036` finding no active shell examples that paste old `/tmp/novaic-cortex-sandbox-*` paths into later commands.
- Remaining ephemeral path references are historical failure examples, prohibitions, or tests: satisfied by the explicit file-level classification in `R036`.
- Focused scan/classification exists: satisfied by `R036` and artifact `.complex-problems/L20260516-222011/artifacts/P047-result.md`.

## Execution Map

- `T040` was executed as a focused repository residue scan and classification pass.
- No code changes were needed because every live ephemeral backing-path reference already served the stable-path contract as a warning, guard, or test.
- Result `R036` records the scan outcome and leaves sibling media/tool-output work to `P048` and `P049`.

## Stress Test

- Plausible failure mode: an agent copies `/tmp/novaic-cortex-sandbox-*` from one shell output and reuses it in a later shell command. The remaining live code/docs now point the opposite way: shell schema guidance says not to reuse backing paths, and Cortex sandbox guard logic rejects those paths. The scan did not find active examples teaching the bad pattern.

## Residual Risk

- Low and non-blocking. Historical/design documents still mention the old pattern for context, but they are not live agent instructions. If future docs add fresh shell examples, the stable-path contract should be rechecked with the same focused scan.

## Result IDs

- R036
