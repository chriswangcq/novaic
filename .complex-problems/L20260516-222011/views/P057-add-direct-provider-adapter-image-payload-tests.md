# P057: Add direct provider adapter image payload tests

Status: done
Parent: P056
Root: P000
Source Ticket: none (none)
Source Check: C050
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/README.md
Ticket(s): T047

## Problem
The provider image payload contract cannot be closed from static inspection alone. Add and run a focused LLM Factory unit test that directly exercises provider adapter image handling, especially the Anthropic conversion path for an OpenAI-style data URL image block.

## Success Criteria
- A focused test proves that an OpenAI-style `image_url` data URL is converted to Anthropic-native image content with structured `source.type=base64`, `media_type`, and `data`.
- The test proves the converted content is not flattened into a plain text base64 string.
- Existing Factory log redaction tests still pass.
- Focused LLM Factory tests are run and recorded.

## Subproblems
- P058: Implement provider adapter image payload test

## Results
- R041

## Latest Check
C053

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/README.md
- Ticket T047: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/tickets/T047.md
- Result R041: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/results/R041.md
- Check C051: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/checks/C051.md
- Check C053: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/checks/C053.md

## Follow-ups
- P058: Implement provider adapter image payload test
