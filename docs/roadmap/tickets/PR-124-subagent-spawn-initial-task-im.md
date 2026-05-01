# PR-124: Spawn delivers initial task via `SUBAGENT_SEND`

## 背景

当前 spawn 创建子 Agent 后写 `SPAWN_SUBAGENT` 消息触发 wake。目标架构希望子 Agent 与父 Agent 都走统一 IM 通路：spawn 只创建子 Agent，初始任务也作为一条发给 child 的 `SUBAGENT_SEND`。

## Scope

- Business spawn endpoint 创建 subagent 后，写入 `SUBAGENT_SEND` 初始任务消息。
- 初始任务消息 metadata 明确包含 `target_subagent_id` 与 `sender_subagent_id`。
- 保留 `SPAWN_SUBAGENT` 类型定义，后续票删除，保证本票可独立 merge。

## 非目标

- 不删除 `SPAWN_SUBAGENT` enum / schema。
- 不删除 LLM 工具。

## 实施计划

- 修改 `/internal/subagents/{agent_id}/spawn` 写消息类型为 `SUBAGENT_SEND`。
- 检查并同步任何仍在写 `SPAWN_SUBAGENT` 的 active Business endpoint。
- 保证 EntityStore 自动生成 outbox `subagent_send`，payload 顶层带 child `subagent_id`。

## 单元测试

- Business spawn 单测：spawn 后消息类型为 `SUBAGENT_SEND`。
- Business spawn 单测：outbox trigger 为 `subagent_send`，payload top-level `subagent_id` 等于新 child id。
- 回归 `dispatch_subscriber` 测试。

## 冒烟测试

- 本地调用 spawn endpoint，确认 child 被创建，且初始任务以 IM 进入 child wake。
- 线上 smoke：创建一个子 Agent，确认第一轮 LLM context 中用户侧 IM 来自 parent/subagent_send，而不是 `SPAWN_SUBAGENT` 特例。

## 部署 Checklist

- Business 测试通过。
- Business 服务部署。
- 线上 SQL/日志确认新 spawn 不再产生 `SPAWN_SUBAGENT` 新消息。

## GitHub / Merge

- 依赖 PR-123。
- Commit message: `refactor(business): deliver spawn task through subagent send im`

