# Repo layout and command entrypoint fact capture

## Problem

Capture top-level repository layout and identify likely test/deploy entry points without running expensive commands. This makes later audits faster and less guessy.

## Success Criteria

- Top-level directories/submodules are summarized.
- Likely test commands, deploy scripts, pyproject/package files, and service entrypoints are identified.
- Evidence is bounded and pointer-oriented.
- No implementation edits are made.
