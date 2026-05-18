# Classify UI Base64 and Data URL Residue

## Problem Definition

P613 must search UI code for remaining base64/data URL/FileReader residue and classify each relevant occurrence so risky raw artifact rendering paths are not left behind.

## Proposed Solution

Run focused `rg` scans for `base64`, `data:image`, `readAsDataURL`, `FileReader`, image source construction, and artifact display terms under UI/front-end code. Inspect each relevant occurrence and classify it as safe intentional usage, test guard, non-image utility, debug/provider request, or risky residue. Remove/follow up on risky residue if found.

## Acceptance Criteria

- Exact residue scans are recorded.
- Relevant occurrences are classified with file pointers.
- Risky UI raw artifact rendering residue is removed or converted into a follow-up.
- Focused tests are run if code changes occur; otherwise scan-only classification explains why tests are sufficient from related P611/P612/P608 runs.

## Verification Plan

Record scan output and cite prior passing focused tests. If any code changes occur, run the nearest focused frontend tests.

## Risks

- Overzealous deletion can break legitimate local media handling such as audio waveform/silent WAV constants.
- Some test files intentionally contain forbidden terms as guardrails.

## Assumptions

- Safe intentional base64 constants are allowed when unrelated to raw artifact/image rendering.
