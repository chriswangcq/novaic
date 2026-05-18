# Foundational boundary residue cleanup and verification

## Problem Definition

P702 must scan for stale or misleading claims that collapse Blob, LogicalFS, or Sandbox responsibilities into Cortex or other higher-level services. It must patch safe active-surface residue and verify guard coverage, without destroying historical roadmap context or intentional regression tests.

## Proposed Solution

Perform this in two stages: first a high-signal residue scan and disposition list, then remediation/verification if scan results show safe cleanup. Focus on active docs, launch scripts, code comments, and guard policies rather than old roadmap/history unless they affect current behavior.

## Acceptance Criteria

- Residue candidates are listed with evidence and classified as active-cleanup, intentional-history, guard/test, or follow-up.
- Safe active residue is patched; unsafe or broad changes are recorded as follow-up.
- Guard checks cover Blob/LogicalFS/Sandbox live RO/RW authority boundaries.
- Focused tests/lints pass after changes.

## Verification Plan

- Run targeted scans for phrases implying Cortex owns Blob bytes, LogicalFS live file authority, or Sandboxd workspace semantics.
- Review existing guard scripts and tests.
- Patch only active high-signal residues.
- Run boundary lints and related tests.

## Risks

- Historical roadmap docs contain intentionally old phrasing; cleaning them aggressively can erase useful design history.
- Broad regexes may flag valid statements about Cortex owning semantics around a file operation.
- Guard tests may intentionally contain retired strings.

## Assumptions

- No backward compatibility is required for active misleading boundary claims.
- If scan finds large architectural gaps, create follow-up rather than pretending to finish inside one cleanup pass.
