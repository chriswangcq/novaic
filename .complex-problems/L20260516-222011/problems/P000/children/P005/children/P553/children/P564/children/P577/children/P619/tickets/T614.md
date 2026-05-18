# Classify UI and Test Multimodal Residue

## Problem Definition

P619 must classify UI and test hits for base64/data URI/image_url/multimodal compatibility terms so intentional guard tests and legitimate UI media paths are not confused with stale compatibility residue.

## Proposed Solution

Scan UI and test directories for relevant terms, cite key slices, classify guard tests and safe UI paths, and run or reuse focused tests when no code change is needed.

## Acceptance Criteria

- Exact UI/test scan is recorded.
- Relevant hits are classified with file pointers.
- Risky reachable residue is removed or followed up.
- Focused UI tests pass if code changes occur; otherwise adjacent passing tests are cited.

## Verification Plan

Use P613/P611/P612 evidence and run focused frontend tests only if new risky paths or code changes appear.

## Risks

- Test files intentionally include base64 strings for redaction guards; do not delete those.

## Assumptions

- This is a classification/audit problem unless scan finds active risky UI compatibility code.
