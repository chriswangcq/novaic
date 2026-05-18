# P130: Provider-native media adapter boundary audit

Status: done
Parent: P003
Root: P000
Source Ticket: T121 (split)
Source Check: none
Package: problems/P000/children/P003/children/P130
Body: problems/P000/children/P003/children/P130/README.md
Ticket(s): T241

## Problem
Some image bytes may legitimately appear at the final provider API boundary as `image_url` or equivalent multimodal content. That transformation must be isolated from Cortex history and must not be confused with text-context leakage.

## Success Criteria
- Provider-native image construction code is mapped and separated from Cortex history projection.
- Blob/display image data is only converted to provider-native media at the final model-call boundary.
- Provider request tests or fixtures prove image content is sent in the expected multimodal format, not as plain text tool history.
- Any stale comments/tests implying base64 text history is acceptable are corrected or classified as provider-boundary-only.
- The design distinction between “history projection” and “provider media payload” is documented in code comments or tests where ambiguity existed.

## Subproblems
- P248: Audit runtime history versus media perception boundary
- P249: Audit provider adapter native media formats
- P250: Classify media/base64 residue as provider-boundary-only or fix it

## Results
- R246

## Latest Check
C261

## Bodies
- Problem: problems/P000/children/P003/children/P130/README.md
- Ticket T241: problems/P000/children/P003/children/P130/tickets/T241.md
- Result R246: problems/P000/children/P003/children/P130/results/R246.md
- Check C261: problems/P000/children/P003/children/P130/checks/C261.md

## Follow-ups
- none
