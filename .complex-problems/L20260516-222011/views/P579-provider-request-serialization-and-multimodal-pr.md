# P579: Provider Request Serialization And Multimodal Projection Inventory

Status: done
Parent: P574
Root: P000
Source Ticket: T569 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P579
Body: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P579/README.md
Ticket(s): T571

## Problem
Audit provider request serialization and multimodal projection paths to verify image/display perception becomes provider-native image content when appropriate, and raw base64/text embedding is not used as a compatibility shortcut. This belongs under P574 because the final API request body determines whether the model actually receives an image.

## Success Criteria
- Records exact scan commands and outputs for provider request builders, multimodal content conversion, image_url/data URL handling, and display perception serialization.
- Reads relevant code/test slices with line references.
- Classifies provider-specific image formatting as intended, risky raw-text/base64 embedding, removable compatibility, or follow-up.
- Identifies whether current-turn display/image content is passed to the provider in a structurally valid way.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- none

## Results
- R566

## Latest Check
C602

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P579/README.md
- Ticket T571: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P579/tickets/T571.md
- Result R566: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P579/results/R566.md
- Check C602: problems/P000/children/P005/children/P553/children/P564/children/P574/children/P579/checks/C602.md

## Follow-ups
- none
