# Classify test and generated-resource media-byte residue

## Problem

Classify media/base64 references in tests and generated/copied resources. Distinguish legitimate fixtures from stale generated copies or tests that encode obsolete contracts.

## Success Criteria

- Test/resource hits are searched and representative files inspected.
- Legitimate fixture usage is separated from stale contract expectations.
- Generated resource duplication is identified and source-of-truth cleanup rules are stated.
- Exact tests/resources needing remediation are listed.
