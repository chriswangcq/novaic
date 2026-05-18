# T569 Result: Runtime LLM Request Projection Path Inventory

## Summary

Runtime LLM request projection is now inventoried through both halves of the path: runtime message assembly/active-stack ordering and provider serialization/multimodal conversion. The inventory did not find a high-confidence runtime projection residue requiring P554 remediation.

## Child Results

- P578 / R565 mapped runtime message assembly and active-stack ordering. It found that Cortex-prepared context is expanded through step refs, current `display` results are classified as `display_perception`, stale stack messages are filtered, and existing tests prove an injected display image message is inserted before the following system/active-stack message.
- P579 / R566 mapped provider serialization. It found that current display perception becomes a provider-native image input, shell stays text-only, history replay is text-only, runtime factory client preserves structured messages, and LLM Factory adapters preserve or convert images for OpenAI/Anthropic/Google.

## Classification

- Intended: current-round `display` perception may produce a user image message for the provider.
- Intended: shell and historical tool results remain terminal/text receipts.
- Intended: active-stack/system messages remain system messages after current-round image injection.
- Intended: LLM Factory logs redact image bytes when request body logging is enabled.
- No high-confidence risky residue was forwarded to P554 by this parent.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p578/runtime-message-assembly-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p578/runtime-message-assembly-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p579/provider-serialization-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p579/provider-serialization-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p579/llm-factory-provider-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p579/llm-factory-provider-slices.txt`
