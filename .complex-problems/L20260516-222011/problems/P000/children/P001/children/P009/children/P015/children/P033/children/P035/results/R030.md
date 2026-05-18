# P035 Result

## What Changed

Test fixture vocabulary cleanup was split and completed through:

- `P038` common tests.
- `P039` runtime tests.
- `P040` Cortex tests.
- `P041` app monitor tests.

## Verification Summary

- Common focused tests: 23 passed.
- Runtime focused tests: 20 + 8 + 10 passed.
- Cortex focused tests: 26 passed.
- App monitor focused tests: 11 passed.

## Residue Classification

- Common: only `audio_qa` negative guard remains.
- Runtime: only `LEGACY_DIRECT_REPLY_TOOL = "im_reply"` and a negative schema assertion remain.
- Cortex: old names remain only in negative tool-schema assertions.
- App tests: `im_reply` remains only behind `LEGACY_DIRECT_REPLY_TOOL` and a non-display assertion.

## Remaining Gap

Production activity projection legacy helpers remain in `P036`, and final repo-wide exception inventory remains in `P037`.
