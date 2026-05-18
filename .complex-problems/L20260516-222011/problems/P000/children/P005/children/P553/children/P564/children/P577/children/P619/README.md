# UI and Test Multimodal Residue Classification

## Problem

Classify UI/test base64/image_url/multimodal search hits so intentional guard tests and UI media paths are separated from stale compatibility residue.

## Success Criteria

- Records exact UI/test scans for base64/data URI/image_url/multimodal terms.
- Classifies relevant hits with file pointers.
- Creates follow-up for risky reachable UI/test residue that hides old behavior.
- Runs focused UI tests if code changes occur.
