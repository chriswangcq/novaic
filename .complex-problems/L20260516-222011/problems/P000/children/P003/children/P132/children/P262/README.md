# Final cross-layer projection marker scan

## Problem

After focused tests are in place, run a final marker scan over the relevant projection/context modules and tests to classify remaining `base64`, `data:image`, `/9j/`, `_mcp_content`, `payload_ref`, `step_ref`, and display projection hits.

## Success Criteria

- Final scan output is summarized and classified.
- No unclassified raw media marker remains in LLM-visible history/text paths.
- Remaining provider-native, current-display, fixture, docs, or crypto/auth hits are explicitly classified.
- Focused cross-layer tests are rerun and pass after any changes.
