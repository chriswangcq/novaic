# PR-111 — Business owns system prompt assembly

## 背景

`task_queue/utils/system_prompt.py` 仍在 Runtime 内本地组装 LLM system prompt；同时 Business 的 `agents.prompts_preview` 还反向 import Runtime 的 prompt builder。这个边界不合理：客户端可以通过 Entangled/Business 通路控制 agent 配置和 prompt 默认片段，最终拼装也应该由 Business 负责，Runtime 只消费结果并写入 Cortex wake scope。

## 目标

- Business 成为 system prompt / wake message 拼装唯一活代码来源。
- Runtime `session.init` 只调用 Business internal endpoint 获取 system prompt。
- 删除 Runtime 旧 `task_queue.utils.system_prompt`，避免新旧逻辑并存。
- 保留 Runtime transient execution-control 文案 `NO_TOOL_WARNING`，但迁到独立模块。

## 实施

- [x] 在 Business 新增 prompt builder，并复用 `prompt_defaults`、agent drive、agent info、skills。
- [x] 在 Business internal API 暴露 `POST /internal/agents/{agent_id}/system-prompt`。
- [x] `agents.prompts_preview` 改为直接调用 Business prompt builder，删除反向 Runtime import。
- [x] Runtime `BusinessClient` 新增 `build_system_prompt(...)`。
- [x] Runtime `handle_session_init` 改为调用 Business endpoint，删除本地 builder 和二次 skill match。
- [x] 删除 Runtime `task_queue/utils/system_prompt.py`，新增专用 `no_tool_warning.py`。
- [x] 更新所有测试和 guardrail，禁止旧 Runtime prompt builder 复活。

## 测试

- [x] Business 单测：prompt builder contract、profile 渲染、main/child 工具差异、preview action。
- [x] Runtime 单测：session init 通过 Business prompt endpoint 注入 system prompt、旧 module 不存在、NO_TOOL_WARNING contract。
- [x] 编译检查：`python -m compileall -q business`、`python -m compileall -q task_queue`。

## 冒烟测试

- [x] Runtime session init 本地单测覆盖 system prompt 插入。
- [x] 部署后检查 Business/Runtime 服务状态。
- [x] 线上/远端确认旧 `task_queue/utils/system_prompt.py` 不存在。

## 部署

- [x] `./deploy business`
- [x] `./deploy runtime`
- [x] `./deploy status`

## GitHub 提交

- [x] `novaic-business` 提交并 push。
- [x] `novaic-agent-runtime` 提交并 push。
- [x] 父仓库 bump 子模块、更新工单状态、提交并 push。
