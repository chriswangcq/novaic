# T449 Result: Aggregate compatibility final matrix

## Summary

Produced the final aggregate compatibility matrix from P453 scan/classification evidence and P454 focused behavior-test evidence. No unresolved dangerous compatibility residue remains in the checked categories.

## Evidence Sources

- P453 / R439 / C465: aggregate guard matrix rerun and classified source/test hit set.
- P454 / R442 / C468: aggregate focused behavior tests.
- P456 / R440 / C466: runtime suite passed, `100 passed`, exit `0`.
- P457 / R441 / C467: Cortex suite passed, `135 passed`, exit `0`.
- Synthesis input artifact: `.complex-problems/L20260516-222011/tmp/p455/evidence-synthesis-input.txt`.

## Final Matrix

| Category | Intended Contract | Scan Evidence | Behavior Evidence | Residual Dangerous Residue |
| --- | --- | --- | --- | --- |
| attach / generation | Attach and outbox paths require generation checks; missing/stale generation is rejected. | P453 classified `missing_generation` as rejection reason and `expected_session_generation` as target attach/outbox contract. | P456 passed generation-checked attach and attach outbox cutover tests. | None found. |
| finalize / remaining stack | Finalize is structured ownership with reason, generation, and remaining stack. | P453 classified `finalize_reason` / `remaining_stack` as intended finalize ownership data. | P456 passed finalize ownership, summary boundary, and scope-end notification tests. | None found. |
| session-ended / notifications | Session-ended events flow through explicit state/session handling, not hidden compatibility paths. | P453 state/finalize/generation scan found no unclassified session-ended residue. | P456 passed session-ended/environment notification related focused tests. | None found. |
| suspected-dead / recovery | Watchdog/dead-session recovery is explicit and generation-aware. | P453 state guard classified recovery/generation hits as target logic. | P456 passed suspected-dead recovery and recovery outbox cutover tests. | None found. |
| archive / scope lifecycle | Cortex archive/scope lifecycle writes are explicit event/summary contracts. | P453 classified archive/finalize diagnostics as intended where generation/stack checks apply. | P457 passed context event lifecycle, skill lifecycle, scope summary, archived summaries, and legacy lifecycle removal tests. | None found. |
| context projection / LLM prepare | Materialized projection endpoints are bridge helpers; `prepare_for_llm` is authoritative LLM context assembly. | P453 classified `/v1/context/read|append|batch` as materialized projection and `/prepare_for_llm` as authoritative prepare. | P457 passed context writes, read-source guards, projection, and store tests. | None found. |
| shell output | Shell returns terminal-like bounded text and structured `tool-output.v1` manifests; history should not inline binary payloads. | P453 classified `tool-output.v1` as the target shell output contract. | P456 passed shell output contract and no historical tool-image injection tests; P457 passed shell capability blob contract. | None found. |
| display / current-turn perception | Display can load current-turn visual input explicitly; history projection keeps pointer/manifest only. | P453 classified display current-turn visual input as explicit perception and history as sanitized. | P457 passed tool/step output projection and context projection tests covering the display/payload boundary. | None found. |
| payload / blob / base64 boundary | Base64 remains only at device/blob/provider/current-turn perception boundaries; historical LLM context uses blob/pointer/manifest. | P453 classified base64 hits as boundary-local and not historical context injection. | P456 historical image guard and P457 payload/projection/shell blob tests passed. | None found. |
| tests / fixtures | Compatibility wording may remain only in negative guards, fixtures, and contract assertions. | P453 classified retained test hits as guard/fixture assertions. | P456/P457 focused guard tests passed. | None found. |

## Conclusion

The final matrix combines source-level guard classification and behavior-level test evidence. Within the audited scope, there is no known unresolved dangerous compatibility residue or old live path.

## Residual Risk

This is not a whole-repo full test run or production smoke test. It proves the targeted compatibility cleanup matrix and focused behavior suites are clean. Broader deployment/runtime smoke should remain separate from this compatibility-final-matrix ticket.
