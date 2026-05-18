# Add exact backend preview boundary evidence and focused tests

## Problem

Close the evidence gap for P603 by collecting exact line-numbered backend slices and focused test output for Agent Monitor/progress preview payload boundaries. The follow-up must prove whether backend monitor/progress paths expose bounded text/payload references and remain separate from LLM request image injection.

## Success Criteria

- Append exact line-numbered slices for `/v1/steps/read_preview`, payload inspection APIs, step payload externalization/indexing, and Business monitor/progress schema or event projection surfaces.
- Run focused tests that directly cover payload externalization, bounded payload preview/read APIs, and Agent Monitor timeline/progress boundary behavior.
- Record whether any backend monitor/progress event path can carry raw image bytes or base64.
- Map evidence back to the original P603 criteria with residual risk explicitly stated.
