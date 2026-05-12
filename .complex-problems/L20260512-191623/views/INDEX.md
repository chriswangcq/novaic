# Complex Problem Ledger

Ledger: L20260512-191623
Schema: v6
Root: P000 - Display image must reach LLM as visual input
Status: done
Updated: 2026-05-12T11:36:34+00:00

## Problem Tree
- [done] P000: Display image must reach LLM as visual input
  - [done] P001: Runtime must inject display images through full LLM preparation
  - [done] P002: Factory logs must show image delivery without raw base64
  - [done] P003: Cortex display projection must not hide missing media as OK

## Active

## Blocked

## Done
- [x] P000: Display image must reach LLM as visual input
- [x] P001: Runtime must inject display images through full LLM preparation
- [x] P002: Factory logs must show image delivery without raw base64
- [x] P003: Cortex display projection must not hide missing media as OK

## Tickets
- [done] T000: Harden display image LLM injection -> P000 (split)
- [done] T001: Add full Runtime display image preparation regression -> P001 (one_go)
- [done] T002: Redact provider-native image data in Factory log snapshots -> P002 (one_go)
- [done] T003: Make empty display perception diagnostic -> P003 (one_go)

## Latest Checks
- [success] C000: P001 P001 is solved. The new test covers the full Runtime preparation path and proves a following `system` message does not suppress current-round display image injection.
- [success] C001: P002 P002 is solved. Factory log snapshots now preserve image delivery markers while redacting raw base64 image bytes for both OpenAI and Anthropic provider message shapes.
- [success] C002: P003 P003 is solved. Empty display perception projection now produces an explicit diagnostic marker instead of `OK`, and existing image projection tests still pass.
- [success] C003: P000 The root problem is solved. The fix does not rely on the previous "old log" explanation alone: it adds executable guardrails at all three boundaries where the issue could recur.
