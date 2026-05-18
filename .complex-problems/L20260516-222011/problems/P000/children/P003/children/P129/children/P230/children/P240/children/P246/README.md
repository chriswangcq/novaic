# Correct stale shell capability wording if found

## Problem

Shell capability guidance may still contain stale wording that implies raw payload/base64 output belongs in normal context or replies. This belongs under P240 because misleading guidance is the practical contract bug users are seeing.

## Success Criteria

- Stale or misleading wording found by the mapping pass is corrected.
- If no correction is needed, the result cites the inspected wording and explains why it is already correct.
- No compatibility or fallback text encourages old direct-tool/raw-output behavior.
