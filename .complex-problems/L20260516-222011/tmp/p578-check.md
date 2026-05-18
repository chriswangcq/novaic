# Runtime Message Assembly And Active Stack Ordering Check

## Summary

P578 is successful. R565 provides durable scans, focused slices, and a clear classification of the runtime message assembly path. The one-go result is acceptable because the child problem was narrow and its riskiest prior symptom, a display image followed by a system/active-stack message, is directly covered by a focused test.

## Evidence

- Scan and slice artifacts:
  - `.complex-problems/L20260516-222011/tmp/p578/runtime-message-assembly-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p578/runtime-message-assembly-slices.txt`
  - `.complex-problems/L20260516-222011/tmp/p578/scan-command-manifest.md`
- Code evidence:
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py:296-367` uses Cortex prepared context and Common assembly.
  - `novaic-common/common/contracts/llm_assembly.py:198-261` builds and appends transient active stack messages while filtering stale snapshots.
  - `novaic-agent-runtime/task_queue/contracts/llm_call.py:115-146` runs step-ref expansion, sanitization, and multimodal processing in order.
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py:119-209` chooses `display_perception` only for current display tool results.
  - `novaic-agent-runtime/task_queue/utils/context.py:76-92` preserves `_projection` only as a temporary multimodal handoff marker.
- Test evidence:
  - `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py:183-190` rejects local runtime stack/tool assembly adapters.
  - `novaic-common/tests/test_llm_assembly_contract.py:73-140` covers transient active stack message behavior and stale stack filtering.
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py:230-285` verifies display image insertion before a following system message.

## Criteria Map

- "Records exact scan commands and outputs": satisfied by scan output, focused slice output, and command manifest.
- "Reads relevant runtime code/test slices with line references": satisfied by the cited runtime, Common assembly, and tests.
- "Classifies tool-result/history/system-message projections": satisfied by R565's hit buckets for Cortex prepare, Common active-stack assembly, step-ref expansion, sanitize, and multimodal handoff.
- "Identifies active-stack ordering risk": satisfied; the risk was explicitly tested and classified as non-blocking because image insertion occurs before the following system message.
- "Captures high-confidence risky residue for P554": satisfied; no high-confidence remediation candidate was found from this branch.

## Execution Map

- T570 was a one-go static classification.
- Execution produced R565 with durable evidence artifacts.
- This check performed no implementation work and judged only the recorded result.

## Stress Test

- Plausible failure mode: active stack system message appended after a display result prevents the display image from being passed to the provider.
- Evidence: the focused test constructs exactly that shape and asserts final role order `assistant`, `tool`, `user`, `system`, with the image in the inserted user message.
- Plausible failure mode: stale stack messages accumulate in history.
- Evidence: Common assembly filters prior active stack snapshots before appending the current transient control-plane message.
- Plausible failure mode: all historical display outputs become images.
- Evidence: step-result projection only marks current display tool results as `display_perception`; older tool messages become `history`.

## Residual Risk

- Provider-specific serialization remains under P579; P578 should not claim that final provider request shape is solved.
- Display tool payload production remains under P575.
- No code was changed in this branch.

## Result IDs

- R565

