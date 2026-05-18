# P580 Scan Command Manifest

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p580
{
  printf '%s\n' '## Display implementation/config scan'
  rg -n 'def .*display|display\(|file_url|modality|blob://|runtime-artifact|_mcp_content|type.*image|mimeType|base64|data:image|emitImage|display' \
    novaic-agent-runtime novaic-cortex novaic-device novaic-common novaic-sandbox-service novaic-sandbox-sdk novaic-app \
    --glob '!**/.git/**' --glob '!**/__pycache__/**' || true
} > .complex-problems/L20260516-222011/tmp/p580/display-implementation-scan.txt
```

```bash
{
  printf '%s\n' '## Runtime display handler normalization/execution'
  nl -ba novaic-agent-runtime/task_queue/handlers/tool_handlers.py | sed -n '80,175p;240,430p'
  printf '\n%s\n' '## Display LLM builtin schema'
  nl -ba novaic-common/common/tools/llm_builtin.py | sed -n '165,205p'
  printf '\n%s\n' '## Tool product semantics display'
  nl -ba novaic-common/common/contracts/tool_product_semantics.json | sed -n '20,40p'
  printf '\n%s\n' '## Resource/blob contracts'
  nl -ba novaic-common/common/contracts/resource_ref.py | sed -n '1,60p'
  nl -ba novaic-common/common/contracts/blob.py | sed -n '1,100p'
} > .complex-problems/L20260516-222011/tmp/p580/display-implementation-slices.txt
```

```bash
{
  printf '%s\n' '## Runtime display handler tests'
  nl -ba novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py | sed -n '1,260p'
  printf '\n%s\n' '## Runtime tool output contract tests'
  nl -ba novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py | sed -n '1,220p'
  printf '\n%s\n' '## Common display definition tests'
  nl -ba novaic-common/tests/test_tool_definitions_contract.py | sed -n '70,105p'
  nl -ba novaic-common/tests/test_cortex_observation_contract.py | sed -n '1,70p'
} > .complex-problems/L20260516-222011/tmp/p580/display-test-slices.txt
```

```bash
rg -n '_EXECUTORS|"display"' novaic-agent-runtime/task_queue/handlers/tool_handlers.py
nl -ba novaic-agent-runtime/task_queue/handlers/tool_handlers.py | sed -n '500,570p'
```
