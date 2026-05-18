# Docs and test media-byte residue classification

## Problem

Classify docs and tests that mention base64/image/media bytes so stale or misleading residue can be separated from legitimate regression fixtures and documentation.

## Success Criteria

- Relevant docs/tests mentioning media bytes are sampled and classified.
- Stale or misleading docs that conflict with the current contract are listed for remediation.
- Legitimate test fixtures are identified as non-remediation evidence.
