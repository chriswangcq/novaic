# Ticket: classify and isolate remaining direct-tool vocabulary

## Problem Definition

The shell-first contract is implemented in many places, but a skeptical scan still finds legacy direct-tool names across tests, activity projection, policy allowlists, and internal API modules. Some references are valid, but the repo does not yet make the distinction mechanically clear.

## Proposed Solution

Perform a residue classification pass and then clean up misleading current-contract references:

1. Build a focused inventory of every remaining direct-tool token from the scan.
2. Categorize each hit as active bug, migration policy allowlist, legacy historical fixture, internal endpoint/API, or false positive.
3. Replace misleading current-contract test fixtures with shell-first examples.
4. Rename or isolate historical fixtures/helpers so they cannot be mistaken for active runtime paths.
5. Add or update focused guard/tests so future scans can distinguish expected exceptions from actual residue.

## Acceptance Criteria

- No current-contract fixture uses direct IM/payload/audio/subagent tool names as the normal active path.
- Remaining direct-tool tokens are intentionally grouped and named as legacy, migration policy, or API endpoint terms.
- Activity projection keeps historical display behavior but makes legacy status unambiguous.
- A focused scan report exists in the result, with every remaining token category accounted for.
- Focused tests for touched modules pass.

## Verification Plan

- Run `rg` for the direct-tool vocabulary and classify every remaining hit.
- Run touched Python tests or py_compile for Python changes.
- Run touched frontend unit tests if ActivityTimeline or projection UI changes.
- Run the relevant shell/tool-surface guard tests.

## Risks

Over-cleaning may delete legitimate compatibility regression coverage. Keep coverage, but rename fixtures and helpers so compatibility intent is explicit.
