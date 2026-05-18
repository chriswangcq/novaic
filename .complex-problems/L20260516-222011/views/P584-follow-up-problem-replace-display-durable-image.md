# P584: Follow-up Problem: Replace display durable image bytes with BlobRef-backed perception fetch

Status: done
Parent: P580
Root: P000
Source Ticket: none (none)
Source Check: C604
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/README.md
Ticket(s): T574

## Problem
P580 found that display public tool history strips image base64 correctly, but `_ok()` still persists `durable_payload.llm_content` containing inline base64 for small images. That is not ordinary shell-visible text, but it is still durable duplicated file bytes inside Cortex/runtime payload state. This conflicts with the infrastructure boundary that Blob Service owns bytes while product services persist BlobRefs and semantics.

## Success Criteria
- Display durable payload stores BlobRef plus MIME/size/metadata, not inline image base64.
- Current-turn display perception still reaches the LLM as provider-native image input.
- The projection path fetches Blob bytes on demand at the current perception boundary or an equivalent explicit media resolver boundary.
- Public tool history remains text-only/placeholder-only.
- Tests that currently assert `durable_payload.llm_content._mcp_content[].data` are updated or removed.
- Focused tests prove no base64 is stored in public content or durable display payload, while provider request still receives the image.

## Subproblems
- P585: Child Problem: Display BlobRef perception design and call-path map
- P586: Child Problem: Implement BlobRef-backed display perception
- P587: Child Problem: Verify display durable no-base64 and image delivery

## Results
- R577

## Latest Check
C614

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/README.md
- Ticket T574: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/tickets/T574.md
- Result R577: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/results/R577.md
- Check C614: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/checks/C614.md

## Follow-ups
- none
