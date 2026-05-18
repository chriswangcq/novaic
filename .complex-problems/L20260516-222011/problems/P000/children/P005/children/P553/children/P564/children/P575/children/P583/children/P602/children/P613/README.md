# UI Base64 Residue Classification

## Problem

Search and classify remaining frontend/UI base64 and data URL code so safe intentional uses are distinguished from risky raw artifact rendering residue.

## Success Criteria

- Records exact scans for `base64`, `data:image`, `readAsDataURL`, `FileReader`, and image source construction under UI code.
- Classifies each relevant occurrence as safe intentional usage, non-image utility, test guard, debug/provider request, or risky residue.
- Removes or follows up on risky residue if found.
- Runs focused tests or records why scan-only classification is sufficient.
