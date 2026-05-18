# write_step payload_ref mirroring audit result

## Summary

`write_step`/`normalize_step` externalizes payloads and mirrors the actual persisted `payload_ref` into both the top-level step and the stored observation. I tightened local-payload test coverage so the observation-level mirror is explicitly verified for both local and blob-backed paths.

## Done

- Mapped payload handling at `novaic-cortex/novaic_cortex/workspace.py:719-735`.
- Verified payload data is removed from step JSON with `normalized.pop("payload")`.
- Verified `write_payload` returns the actual persisted ref and that ref is written to `normalized["payload_ref"]` and `normalized["observation"]["payload_ref"]`.
- Added local-path assertion in `test_write_step_externalizes_payload_and_indexes_payload_ref` so stored observation mirroring is checked, not just top-level ref.
- Confirmed blob-backed path already checks observation mirroring in `test_write_step_externalizes_large_payload_to_blob_ref`.

## Verification

- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_step_index_outcome.py novaic-cortex/tests/test_payload_inspection_api.py`.
- Result: `26 passed in 0.42s`.

## Known Gaps

- This result does not judge whether every active API call site reaches `write_step`; that is covered by `P148`.
- This result does not judge step index completeness beyond payload ref presence; that is covered by `P147`.

## Artifacts

- Modified `novaic-cortex/tests/test_step_index_outcome.py`.
