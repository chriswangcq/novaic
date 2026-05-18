# Sandbox Wire Base64 and Mount Residue Classification Result

## Summary

Closed P622 split children. Base64 and mount residue were separated and classified: base64 bytes stay in private wire/durable payload/current multimodal perception surfaces rather than public history/tool text, and mount ownership is layered as SDK DTO -> Cortex LogicalFS plan -> sandboxd service namespace execution.

## Done

- P628 classified base64/public-history surfaces and verified backend/frontend redaction/projection tests.
- P629 classified mount ownership/bypass surfaces and verified SDK/service/Cortex mount/logicalfs tests.
- No public raw base64 history leak or client-side/runtime mount bypass was found.

## Verification

- P628 check C660 succeeded, citing R619; Python focused suite 50 passed; frontend suite 18 passed.
- P629 check C661 succeeded, citing R620; mount/logicalfs focused suite 24 passed.

## Known Gaps

- `step_result_projection.py` retains legacy inline image-data parser compatibility, but current artifact/BlobRef history paths are guarded by tests.
- Generated untracked `__pycache__` files remain for final workspace hygiene.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p628-base64-history-classification.md`
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-classification.md`
- `.complex-problems/L20260516-222011/tmp/p628-base64-history-python-tests.txt`
- `.complex-problems/L20260516-222011/tmp/p628-base64-history-frontend-tests.txt`
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-tests.txt`
