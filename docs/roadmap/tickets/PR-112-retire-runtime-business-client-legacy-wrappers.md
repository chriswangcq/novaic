# PR-112 — Retire Runtime BusinessClient legacy business-data wrappers

## 背景

PR-111 后，system prompt/skills/drive/profile 的拼装和默认值已经归 Business 所有。Runtime `BusinessClient` 里仍残留一批旧 wrapper：`get_agent_info`、`get_agent_drive`、`get_agent_state`、`get_main_subagent`、`get_agent_skills`、`match_skills_for_task`、`get_quadrant_task_board_by_subagent`。这些方法在 Runtime 活代码里已经无调用，但保留会制造“Runtime 也能自己拉业务数据拼语义”的假路径。

## 目标

- 删除 Runtime `BusinessClient` 未使用的旧业务数据 wrapper。
- 删除 `broadcast_url` 这种 ignored back-compat 参数。
- 保留 Runtime 真实需要的最小通路：`entity_*`、message transition、`build_system_prompt`、broadcast、recover、due-wake。
- 增加 guardrail，防止旧 wrapper 回流。

## 实施

- [x] 删除 `BusinessClient.__init__(broadcast_url=...)` ignored 参数。
- [x] 删除 agent drive/info/state/skills/quadrant task wrapper。
- [x] 增加 Runtime 边界测试：`BusinessClient` 不再暴露旧 wrapper。
- [x] 确认全仓没有旧 wrapper 调用点。

## 测试

- [x] `cd novaic-agent-runtime && python -m pytest tests/test_pr112_business_client_boundary.py tests/test_llm_prompt_contract.py tests/test_pr65_agent_root_scope.py tests/test_session_init_message_ids.py tests/test_wake_im_replay.py`
- [x] `cd novaic-agent-runtime && python -m compileall -q task_queue`

## 冒烟测试

- [x] `./deploy runtime`
- [x] `./deploy status`
- [x] 远端 grep 确认旧 wrapper 不存在。

## 部署

- [x] Runtime 已部署。

## GitHub 提交

- [x] `novaic-agent-runtime` 提交并 push。
- [x] 父仓库 bump 子模块、更新工单状态、提交并 push。
