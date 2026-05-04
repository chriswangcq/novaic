# PR-130: Promote `display` to a real LLM + Runtime tool

## 背景

用户附件提示词已经要求 Agent 在需要查看图片/文件时调用 `display(file_url=...)`，但 `display` 还没有进入 canonical LLM tool schema，也没有 Runtime executor。这会让模型看到不可执行能力，属于幽灵工具。

## Scope

- 将 `display` 加入 `common.tools.llm_builtin.AGENT_BUILTIN_TOOL_SCHEMAS`。
- 将 common 产品工具目录里的 `multimodal.display` 改为从 canonical LLM schema 适配。
- 在 Runtime `tool_handlers` 中实现 `display` executor：
  - 只解析 BlobRef 文件引用。
  - 使用 `X-User-ID` 从 Blob Service 拉取文件字节。
  - 图片按 `_mcp_content` image 返回给 LLM；文本按 `_mcp_content` text 返回；其他二进制返回 metadata 文本。
- 修正 Cortex step result projection：Runtime 保存 step result 时若是 JSON 字符串，投影层需要解析其中的 `_mcp_content`，否则下一轮 LLM 只能看到 JSON 文本。
- 给 execution log 增加用户可理解的 display 摘要。

## 非目标

- 不做外部任意 URL 抓取。
- 不把附件原始 base64 直接塞进 user message。
- 不实现音频问答。

## 单元测试

- Common：`display` 出现在 canonical schema 与 `MULTIMODAL_TOOLS`，且 metadata 由 canonical schema 适配。
- Runtime：`display` 能把小图片转换为 `_mcp_content` image；缺 user_id / 不支持 URL / 404 走失败分支。
- Cortex：tool schema 名单包含 `display`；step result projection 能解析 JSON 字符串里的 `_mcp_content`。

## 冒烟测试

- 发送带图片附件消息，LLM 调用 `display(file_url=...)` 后能看到图片内容或文本占位。
- execution log 展示“已查看文件/附件”，不展示 debug payload。

## 部署 Checklist

- Common / Cortex / Runtime 相关测试通过。
- 部署 Common、Cortex、Runtime。
- 线上确认 LLM request tools 中出现 `display`，且 Runtime executor 不再报 `Unknown tool: display`。

## GitHub / Merge

- 可单独 merge。
- Commit message: `feat(tools): add display runtime tool`

## Closure — 2026-05-01

- Status: verified closed and deployed.
- Verification: Common tool contract, Cortex tool-schema, Runtime tool-path, and execution-log display tests passed.
- Current architecture: `display` is an active Common schema + Runtime executor tool.
