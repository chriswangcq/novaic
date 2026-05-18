# Check P789 Cortex Projection Contract Inspection

## Summary
`P789` succeeds as an inspection problem. It identified the exact unsafe compatibility path, the safe BlobRef path, and the tests that must change.

## Evidence
- `R769` names the active parser and formatter functions.
- `R769` lists tests that preserve inline `data` image behavior.
- `R769` lists tests that preserve desired BlobRef `image_ref` behavior.

## Criteria Map
- Exact projection functions and tests identified: success.
- Active unsafe compatibility behavior described with evidence: success.
- Patch scope and test locations explicit: success.
- No product code modified: success.

## Execution Map
- Read `step_result_projection.py`.
- Searched and read focused Cortex tests.
- Recorded patch plan for `P790`.

## Stress Test
- The inspection distinguishes display perception with `blob://` image refs from unsafe inline base64 image data.
- It does not recommend removing display entirely.

## Residual Risk
- None for inspection; code cleanup remains in `P790`.

## Result IDs
- Checked result: `R769`.
