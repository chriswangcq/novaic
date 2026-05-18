# Classify media/base64 residue as provider-boundary-only or fix it

## Problem

Search results may still show `data:image`, `/9j/`, or base64-like fixtures. Those occurrences must either be tests for provider/display boundaries or be fixed if they imply normal history leakage. This belongs under P130 because residue can confuse future maintainers and agents.

## Success Criteria

- Residue scan across runtime, Cortex, common, and LLM factory media paths is recorded.
- Any live code/comment that treats base64 as ordinary text history is corrected.
- Remaining base64/media fixtures are documented as test/provider-boundary-only.
