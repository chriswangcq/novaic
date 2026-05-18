# Runtime Queue Cortex service-code residue discovery check

## Summary

Status: success.

`R737` satisfies this discovery child. It scanned Runtime/Queue/Cortex code, separated guardrail/test/protocol hits from active remediation candidates, and did not modify code.

## Evidence

- `R737` records two targeted scan families: legacy/fallback/direct terms and media/display/blob/logicalfs/sandbox terms.
- `R737` spot-read the most relevant active files:
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
  - `novaic-cortex/novaic_cortex/sandbox.py`
  - `novaic-agent-runtime/task_queue/tool_surface_policy.py`
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `R737` lists exact remediation candidates for the next child.

## Criteria Map

- Runtime/Queue/Cortex source and tests scanned: satisfied.
- Findings classified: satisfied; guardrail tests and intentional protocol/auth encodings were not treated as stale active code.
- Exact remediation candidates listed: satisfied.
- No code modified in this ticket: satisfied by execution scope.

## Execution Map

- This was a read-only one-go discovery ticket after prior split.
- It produced remediation candidates but did not patch them.
- The next remediation child can act directly on the listed files without repeating the broad scan.

## Stress Test

- Checked that `legacy/fallback/direct` matches were not automatically considered bugs; many are tests enforcing deletion of old paths.
- Checked the current shell execution code against the desired sandboxd/LogicalFS boundary and found it aligned.
- Checked display/base64-related code and found a precise compatibility surface rather than uncontrolled history leakage.

## Residual Risk

This closes only Runtime/Queue/Cortex code discovery. Gateway/Business/Device and infra/VMuse discovery remain open under sibling children.
