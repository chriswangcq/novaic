# P606: Frontend Timeline Preview Truncation and Escaping

Status: done
Parent: P604
Root: P000
Source Ticket: T597 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/README.md
Ticket(s): T598

## Problem
Audit the Agent Monitor timeline/list preview rendering path to ensure tool outputs shown inline are escaped, bounded, and summarized, rather than rendering raw large tool result text such as base64 screenshots.

## Success Criteria
- Records exact scans for timeline/list preview components and helper functions.
- Cites frontend slices showing escaping, truncation, or preview-only rendering.
- Runs focused tests if available, or records missing test coverage as a gap.
- Creates a follow-up if inline timeline preview can render raw unbounded image/base64 text.

## Subproblems
- P609: Redact raw payload-like text in ActivityTimeline details

## Results
- R590

## Latest Check
C631

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/README.md
- Ticket T598: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/tickets/T598.md
- Result R590: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/results/R590.md
- Check C629: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/checks/C629.md
- Check C631: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P606/checks/C631.md

## Follow-ups
- P609: Redact raw payload-like text in ActivityTimeline details
