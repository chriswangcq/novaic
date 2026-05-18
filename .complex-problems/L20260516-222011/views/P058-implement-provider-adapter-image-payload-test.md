# P058: Implement provider adapter image payload test

Status: done
Parent: P057
Root: P000
Source Ticket: none (none)
Source Check: C051
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/children/P058
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/children/P058/README.md
Ticket(s): T048

## Problem
Add the missing LLM Factory provider adapter test and run the focused verification. This follow-up exists because the previous ticket attempt only prepared the ticket state and did not perform the implementation.

## Success Criteria
- A test directly exercises the Anthropic provider conversion path with a synthetic OpenAI-style `data:image/...;base64,...` image URL content block.
- The test asserts the adapter returns a provider-native image block with structured `source.type=base64`, `media_type`, and `data`.
- The test asserts the image payload was not converted into a plain text base64 block.
- Existing chat-route image redaction tests pass together with the new provider adapter test.

## Subproblems
- none

## Results
- R042

## Latest Check
C052

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/children/P058/README.md
- Ticket T048: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/children/P058/tickets/T048.md
- Result R042: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/children/P058/results/R042.md
- Check C052: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/children/P057/children/P058/checks/C052.md

## Follow-ups
- none
