# P578 Scan Command Manifest

## Broad Runtime Scan

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p578
{
  printf '%s\n' '## Runtime message/context assembly terms'
  rg -n 'context\.prepare|prepare_context|build.*context|messages\]|messages =|role.*tool|tool_call_id|_mcp_content|active skill stack|Active skill stack|skill stack|system.*content|request_body|LLM|factory|model_messages|chat.completions|responses' novaic-agent-runtime

  printf '\n%s\n' '## Media/base64/image terms in runtime assembly candidates'
  rg -n 'base64|image_url|display_perception|display|artifact|blob://|multimodal|_mcp_content|tool-output\.v1' novaic-agent-runtime
} > .complex-problems/L20260516-222011/tmp/p578/runtime-message-assembly-scan.txt
```

## Focused Evidence Slices

```bash
{
  printf '%s\n' '## Cortex prepare LLM context handler'
  nl -ba novaic-agent-runtime/task_queue/handlers/cortex_handlers.py | sed -n '293,370p'

  printf '\n%s\n' '## Common LLM assembly active stack insertion'
  nl -ba novaic-common/common/contracts/llm_assembly.py | sed -n '94,310p'

  printf '\n%s\n' '## LLM call handler and explicit prepare contract'
  nl -ba novaic-agent-runtime/task_queue/handlers/llm_handlers.py | sed -n '68,145p'
  nl -ba novaic-agent-runtime/task_queue/contracts/llm_call.py | sed -n '1,150p'

  printf '\n%s\n' '## Step result expansion and display projection decision'
  nl -ba novaic-agent-runtime/task_queue/utils/step_result_client.py | sed -n '75,210p'

  printf '\n%s\n' '## Sanitize and multimodal handoff marker preservation'
  nl -ba novaic-agent-runtime/task_queue/utils/context.py | sed -n '1,190p'

  printf '\n%s\n' '## Tests: active stack and context assembly'
  nl -ba novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py | sed -n '19,70p;138,190p'
  nl -ba novaic-common/tests/test_llm_assembly_contract.py | sed -n '61,140p'

  printf '\n%s\n' '## Tests: display image before following system'
  nl -ba novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py | sed -n '220,285p'
} > .complex-problems/L20260516-222011/tmp/p578/runtime-message-assembly-slices.txt
```

