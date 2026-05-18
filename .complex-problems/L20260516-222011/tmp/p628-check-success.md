# P628 Success Check

## Summary

P628 is solved. The one-go audit is acceptable because it mapped each base64 surface to ownership and verified both backend projection and frontend monitor redaction. No active public-history raw base64 leak remains visible.

## Evidence

- `p628-base64-history-scan.txt` records exact cross-repo base64/history scans.
- `p628-base64-history-slices.txt` cites SDK wire handling, runtime shell/display projection, Cortex shell capability wrapping, step projection, no-history tests, and frontend redaction.
- `p628-base64-history-classification.md` classifies private wire, durable payload, public history, current perception, compatibility, and tests.
- `p628-base64-history-python-tests.txt` shows 50 tests passed.
- `p628-base64-history-frontend-tests.txt` shows 18 tests passed.

## Criteria Map

- Exact base64/stdout/stderr/data URL scans recorded: satisfied.
- Wire encode/decode classified private: satisfied.
- Public LLM-history/tool-text surfaces cited and bounded/manifest-only: satisfied.
- Focused shell/artifact/no-history tests pass: satisfied.
- Follow-up for raw base64 public-history path: not needed; none found.

## Execution Map

- Set P628/T624 executing.
- Captured scan and source/test slices.
- Ran Python backend projection tests.
- Ran frontend monitor redaction tests.
- Recorded R619.

## Stress Test

The check distinguishes three cases that were previously easy to conflate: private sandboxd wire bytes, current multimodal image perception for the LLM API, and historical/public tool text. Tests explicitly assert raw screenshot bytes do not replay into history and monitor details redact raw payloads.

## Residual Risk

Legacy inline image-data parser compatibility remains in `step_result_projection.py`, but current artifact/BlobRef history paths are tested. This is non-blocking unless the user later chooses to delete all historical compatibility parsers.

## Result IDs

- R619
