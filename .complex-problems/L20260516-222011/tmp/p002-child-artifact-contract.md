# Blob Artifact and Display Contract Audit

## Problem

CLI tools that produce media or large outputs should return text plus artifact manifests, with display consuming blob refs without reinserting raw base64 into context.

## Success Criteria

- Inspect artifact manifest helpers and display projection tests.
- Verify screenshot/media CLI returns blob artifacts rather than base64 text.
- Verify display/tool history projection remains sanitized.
- Fix or route any contract gap.
