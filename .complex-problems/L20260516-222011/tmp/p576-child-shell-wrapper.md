# Shell Wrapper Terminal Output Boundary

## Problem

Audit shell execution/wrapper output paths to verify shell tool results shown to LLM are bounded terminal text plus artifact manifests, not raw media/base64 payloads.

## Success Criteria

- Records scans for shell wrapper, tool-output contract, truncation, artifact manifest, and devicectl wrappers.
- Cites code slices showing bounded text and BlobRef artifact manifest behavior.
- Runs focused shell output contract tests.
- Creates follow-up if shell history can inline raw media/base64 output.
