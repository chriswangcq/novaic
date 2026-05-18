# P576: Shell History Tool Output Contract Inventory

Status: done
Parent: P564
Root: P000
Source Ticket: T568 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P576
Body: problems/P000/children/P005/children/P553/children/P564/children/P576/README.md
Ticket(s): T607

## Problem
Audit shell/tool output projection paths to verify shell returns bounded terminal text and durable artifact manifests, while full details remain recoverable through Cortex RO step/payload files. This belongs under P564 because shell is now the main interface class for many tools and must not leak large media/base64 into LLM history.

## Success Criteria
- Records exact scan commands and outputs for shell tool wrappers, truncation/projection code, monitor display summaries, and Cortex step/payload recording.
- Reads relevant code/test slices with line references.
- Classifies output truncation, artifact manifests, payload refs, and full-output storage paths as intended, risky, removable, or follow-up.
- Verifies the current contract: bounded terminal text in LLM history, full output discoverable via RO/payload files, artifacts referenced by BlobRef.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- P614: Shell Wrapper Terminal Output Boundary
- P615: Cortex Shell Step and Payload Persistence Boundary
- P616: Shell Output Contract Test and Guardrail Inventory

## Results
- R606

## Latest Check
C647

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P576/README.md
- Ticket T607: problems/P000/children/P005/children/P553/children/P564/children/P576/tickets/T607.md
- Result R606: problems/P000/children/P005/children/P553/children/P564/children/P576/results/R606.md
- Check C647: problems/P000/children/P005/children/P553/children/P564/children/P576/checks/C647.md

## Follow-ups
- none
