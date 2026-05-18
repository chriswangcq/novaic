# Ticket: final direct-tool residue scan and exception ledger

## Problem Definition

After targeted cleanup, perform a final repo-wide scan for old direct-tool vocabulary and classify every remaining hit. This prevents recurring ambiguous residue and avoids falsely declaring the shell-first contract clean.

## Proposed Solution

- Run focused repo-wide scan excluding generated ledger/dashboard artifacts.
- Classify remaining hits as:
  - migration policy denylist,
  - negative guard assertion,
  - explicit legacy fixture,
  - internal endpoint/API,
  - documentation reference to shell CLI,
  - unresolved residue.
- If unresolved residue exists, create a follow-up rather than close.

## Acceptance Criteria

- A final exception inventory artifact exists.
- No unclassified current-path direct-tool residue remains.
- Focused tests already run by child problems are referenced.

## Verification Plan

- `rg` direct-tool vocabulary across repo with sensible generated/artifact exclusions.
- Spot-check representative remaining categories.

## Risk

The scan may find legitimate route names or negative tests. The goal is classification, not blindly deleting all old strings.
