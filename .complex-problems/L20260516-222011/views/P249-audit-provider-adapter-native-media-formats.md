# P249: Audit provider adapter native media formats

Status: done
Parent: P130
Root: P000
Source Ticket: T241 (split)
Source Check: none
Package: problems/P000/children/P003/children/P130/children/P249
Body: problems/P000/children/P003/children/P130/children/P249/README.md
Ticket(s): T243

## Problem
LLM factory provider adapters must convert image content to provider-native media payloads rather than plain text base64. This belongs under P130 because it is the final API boundary where image bytes are legitimate.

## Success Criteria
- OpenAI/Anthropic/Gemini provider media conversion code is mapped, or absent providers are explicitly scoped.
- Focused tests prove data URL image content is converted to native provider structures, including Gemini inlineData where relevant.
- No provider request test expects raw base64 as a plain text message.

## Subproblems
- none

## Results
- R240

## Latest Check
C255

## Bodies
- Problem: problems/P000/children/P003/children/P130/children/P249/README.md
- Ticket T243: problems/P000/children/P003/children/P130/children/P249/tickets/T243.md
- Result R240: problems/P000/children/P003/children/P130/children/P249/results/R240.md
- Check C255: problems/P000/children/P003/children/P130/children/P249/checks/C255.md

## Follow-ups
- none
