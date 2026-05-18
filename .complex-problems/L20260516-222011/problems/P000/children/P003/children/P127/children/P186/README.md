# Historical display and artifact manifest projection

## Problem

Historical display/tool outputs and generic artifacts must remain manifest/placeholder-only. They should not reintroduce base64, blob bytes, or large payload text into future history.

## Success Criteria

- Map history projection for display, artifact, payload, blob, and generic tool outputs.
- Prove historical display results use history/text projection rather than display perception.
- Prove artifact manifests survive while raw bytes stay out of public context.
- Fix or split any historical projection branch that leaks raw media.
