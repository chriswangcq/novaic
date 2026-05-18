# Check: Durable shell/display base64-absence coverage is complete

## Summary

Success. The parent problem was correctly split by layer and every layer now has direct scan/test evidence: shell CLI, runtime display handler, and Cortex projection all protect against raw base64 durable output.

## Evidence

- `R584` summarizes three successful child results:
  - `R581` / P597: shell CLI BlobRef manifest and no raw base64.
  - `R582` / P598: display handler durable `image_ref`/`display_files` and no inline `data`.
  - `R583` / P599: Cortex projection BlobRef no-inline behavior.
- P597 check `C619`, P598 check `C620`, and P599 check `C621` are successful.
- Combined focused test count for these children: 10 tests passed.

## Criteria Map

- Exact scans for base64/data-url assertions: satisfied by P597/P598/P599 artifacts.
- Shell screenshot BlobRef artifact manifest coverage: satisfied by P597.
- Display durable `image_ref`/metadata without inline `data`: satisfied by P598.
- Concrete follow-up if missing: not needed; no missing direct coverage found.
- Belongs under P582 split: satisfied; this child covers durable output only.

## Execution Map

- `T587` was split into three child problems because the durable contract spans independent shell, display, and Cortex layers.
- Each child performed read-only inventory plus focused pytest.
- No code changes were needed for this parent.

## Stress Test

- Plausible failure mode: screenshot bytes leak through a different layer despite one layer being fixed.
- The split explicitly tested all three boundaries: CLI stdout, runtime durable payload, and Cortex projection.

## Residual Risk

- Current provider-bound image injection is intentionally outside durable output and covered by P593.
- Active-stack/current-round ordering has its own sibling P596.

## Result IDs

- R584
- R581
- R582
- R583
