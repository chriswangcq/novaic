# P000: Audio QA tool schema cutover to shell

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
`audio_qa` remains a direct LLM-facing tool. The target surface should keep display as the special visual/file perception tool, while other interface actions move behind shell capabilities. Audio transcription/QA can be represented as an explicit shell media command with file URLs and prompts.

## Success Criteria
- LLM-visible builtin schemas no longer include `audio_qa`.
- Shell schema advertises `agentctl media audio-qa`.
- The shell command fetches a Blob audio object, resolves the configured audio model, calls Factory, and returns JSON text output.
- Runtime guard tests classify direct `audio_qa` as schema-cutover compatibility only.
- Targeted tests cover schema cutover and the shell audio command path.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
