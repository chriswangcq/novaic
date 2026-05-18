# Ticket: Audit Timeline Preview Rendering

## Problem Definition

Agent Monitor timeline/list preview should show safe, bounded human summaries of tool outputs. Inline timeline rows must not render raw huge tool text, screenshot base64, or unescaped HTML.

## Proposed Solution

Find the frontend timeline/list components and any preview helper code with `rg`, capture exact line-numbered slices for truncation/escaping/preview decisions, and run focused tests if available. If no focused tests exist, record that as a gap for problem-level checking.

## Acceptance Criteria

- Timeline/list preview source files and helpers are identified.
- Exact slices demonstrate bounded and escaped preview rendering, or identify the missing boundary.
- Base64/image text risk is explicitly checked in normal inline timeline rendering paths.
- Verification output or missing-test gap is recorded.

## Verification Plan

Use read-only source scans and focused frontend tests where present. Treat missing bounds/escaping or unbounded raw base64 rendering as a failure requiring follow-up.

## Risks

- Timeline preview may be schema-driven or shared with other list components, making the component names non-obvious.
- Browser-rendered truncation may be CSS-based; source audit should distinguish CSS visual truncation from actual data truncation.

## Assumptions

- This ticket does not change UI code unless a concrete bug is found and spawned as a child problem.
