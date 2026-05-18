# Cortex Payload CLI Coverage Audit

## Problem

`cortex payload read/search/summarize/qa` must be available through the stable shell CLI and advertised in shell schema/help, replacing direct payload LLM tools.

## Success Criteria

- Locate payload CLI implementation and help.
- Verify shell schema advertises payload read/search/summarize/qa.
- Run focused payload CLI/help/API contract tests.
- Fix bounded coverage gaps found.
