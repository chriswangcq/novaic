# T573 Result: Display Tool Implementation And Blob Artifact Contract Inventory

## Summary

Display implementation is aligned with the current contract: it accepts only BlobRefs, fetches bytes from Blob Service with tenant context, emits visual MCP content only inside the executor result, strips image bytes from public tool history, and stores the visual payload separately as display LLM content for the current perception path. No P554 remediation is forwarded from this implementation-layer ticket.

## Evidence

- Display is an active runtime executor in the unified tool dispatch table; see `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:514-520`.
- Display schema tells the LLM to pass BlobRefs only and says images are visual content when small, text files as text, and large/unsupported binaries as concise placeholders; see `novaic-common/common/tools/llm_builtin.py:173-197`.
- Shared BlobRef/resource contracts require `blob://{namespace}/{blob_id}` references; see `novaic-common/common/contracts/resource_ref.py:28-33` and `novaic-common/common/contracts/blob.py:75-85`.
- Runtime display validates BlobRefs and rejects non-Blob refs; see `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:343-350`.
- Runtime display fetches the blob through Blob Service with `X-Tenant-ID`; see `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:400-422`.
- Runtime display creates MCP image content only for images below `_DISPLAY_INLINE_BUDGET_BYTES`; too-large images and unsupported binaries become text placeholders; see `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:323-397`.
- Public tool history strips image `data` and replaces it with a placeholder; see `_display_public_output` at `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:118-139`.
- `_ok` persists the stripped public content as the visible tool content and separately attaches a `durable_payload` for display LLM content; see `novaic-agent-runtime/task_queue/handlers/tool_handlers.py:245-263`.
- Tests verify display is registered, only accepts BlobRefs, fetches Blob Service images, strips image bytes from wrapped public content, and stores the LLM content separately; see `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py:48-101`.
- Tool product semantics say the monitor should show file summary, not embedded raw bytes; see `novaic-common/common/contracts/tool_product_semantics.json:27-33`.

## Classification

- Intended: `display(file_url=blob://...)` is the only supported input path.
- Intended: display executor may create private `_mcp_content` image data for current perception.
- Intended: public tool history contains placeholders, not base64 image bytes.
- Intended but worth remembering for future design: `durable_payload.llm_content` currently stores inline base64 for small current-perception images. This is not shell-visible output or public history, but it is the private payload mechanism used by current runtime projection.
- No risky implementation residue found in this layer.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p580/display-implementation-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p580/display-implementation-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p580/display-test-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p580/scan-command-manifest.md`
