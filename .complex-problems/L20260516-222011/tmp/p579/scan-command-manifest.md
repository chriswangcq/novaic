# P579 Scan Command Manifest

## Runtime client and multimodal projection

```bash
{
  printf '%s\n' '## Provider serialization and multimodal terms'
  rg -n 'image_url|data:image|base64|multimodal|process_multimodal|provider|chat/completions|messages|content\]|content =|FactoryLLMClient|internal_sync_client|request_body|json=' \
    novaic-agent-runtime/task_queue \
    novaic-agent-runtime/tests/unit/task_queue \
    novaic-agent-runtime/tests/test_runtime_explicit_contracts.py

  printf '\n%s\n' '## Factory/client structured content tests'
  rg -n 'structured_image|image_url|data:image|captured\["json"\]|messages\]\[0\]|chat\(' \
    novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py \
    novaic-agent-runtime/task_queue/factory_client.py \
    novaic-agent-runtime/task_queue/contracts/llm_call.py \
    novaic-agent-runtime/task_queue/utils/multimodal.py
} > .complex-problems/L20260516-222011/tmp/p579/provider-serialization-scan.txt
```

```bash
{
  printf '%s\n' '## Runtime multimodal processing'
  nl -ba novaic-agent-runtime/task_queue/utils/context.py | sed -n '183,290p'
  nl -ba novaic-agent-runtime/task_queue/utils/multimodal.py | sed -n '1,155p'

  printf '\n%s\n' '## LLM prepare contract and factory client passthrough'
  nl -ba novaic-agent-runtime/task_queue/contracts/llm_call.py | sed -n '115,146p'
  nl -ba novaic-agent-runtime/task_queue/factory_client.py | sed -n '20,88p'

  printf '\n%s\n' '## Factory client structured image test'
  nl -ba novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py | sed -n '1,80p'

  printf '\n%s\n' '## Runtime current display and history replay tests'
  nl -ba novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py | sed -n '48,90p;190,290p;291,470p'
} > .complex-problems/L20260516-222011/tmp/p579/provider-serialization-slices.txt
```

## LLM Factory service side

```bash
{
  printf '%s\n' '## LLM factory multimodal/provider serialization terms'
  rg -n 'image_url|data:image|base64|messages|content|chat.completions|chat/completions|openai|anthropic|provider|request_body|response_body|json=' novaic-llm-factory || true
} > .complex-problems/L20260516-222011/tmp/p579/llm-factory-provider-scan.txt
```

```bash
{
  printf '%s\n' '## Chat route request logging and provider input'
  nl -ba novaic-llm-factory/factory/routes/chat_routes.py | sed -n '91,230p'
  printf '\n%s\n' '## Providers multimodal conversion'
  nl -ba novaic-llm-factory/factory/providers.py | sed -n '1,280p'
  printf '\n%s\n' '## Factory DB/redaction helpers'
  nl -ba novaic-llm-factory/factory/db.py | sed -n '1,180p'
} > .complex-problems/L20260516-222011/tmp/p579/llm-factory-provider-slices.txt
```

```bash
nl -ba novaic-llm-factory/factory/contracts.py | sed -n '1,240p'
nl -ba novaic-llm-factory/factory/providers.py | sed -n '280,520p'
nl -ba novaic-llm-factory/tests/test_chat_routes.py | sed -n '145,360p'
```
