# P817 Check: Factory Logs Safe Projection Helper

## Verdict

`success`

## Summary

The helper-only child problem is solved. The static page now contains deterministic projection helpers with bounded string, base64/data URL, array, object, depth, and BlobRef behavior, and the helper was tested by extracting and executing the actual code from the HTML file.

## Criteria Map

- Helper functions exist near existing utilities: satisfied at `factory-logs.html` utility section.
- Helper returns display-safe values: satisfied by `projectValue`, `projectedJson`, and `projectedText`.
- Long/base64/media-like values summarized without raw bytes: satisfied by Node sample check.
- Short scalars and BlobRefs remain readable: satisfied by Node sample check.
- Renderer wiring not required in this ticket: satisfied; wiring remains for child problem `P818`.

## Evidence

- Result `R797`.
- `git diff --check` passed for `static/factory-logs.html`.
- Node extraction check printed `projection_helper_ok`.

## Stress Test

The first helper sample failed because base64 detection looked only at the beginning of the string. The implementation was corrected to inspect the full compact string's character-class signals, then the sample passed. This closes the most likely one-go blind spot.

## Residual Risk

No P817-scoped residual risk remains. The helper still must be wired into renderers by `P818`.
