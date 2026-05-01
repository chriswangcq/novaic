# PR-132: Quarantine `audio_qa` until Runtime executor exists

## 背景

`audio_qa` 是有价值能力，但当前没有 Runtime executor。如果继续暴露，会把模型引向不可执行工具。用户要求：保留，但必须接 Runtime executor，否则先不要暴露。

## Scope

- 从 active common tool catalog 中移除 `audio_qa` 暴露。
- 保留设计说明：`audio_qa` 只有在 Runtime executor 和底层音频模型/Factory 调用链打通后才能重新暴露。
- 增加 guardrail：LLM tools 与 `BUILTIN_TOOLS` 都不包含 `audio_qa`。

## 非目标

- 本票不实现音频模型调用。
- 不删除未来 `audio_qa` 设计意图。

## 单元测试

- Common：`audio_qa` 不在 `BUILTIN_TOOLS` / canonical LLM schema 中。
- Runtime：executor 表不包含 `audio_qa`。
- Cortex：LLM tool schema 不包含 `audio_qa`。

## 冒烟测试

- LLM request tools 中不出现 `audio_qa`。
- 上传音频不会诱导模型调用不存在的 `audio_qa`。

## 部署 Checklist

- Common / Cortex / Runtime 测试通过。
- 部署 Common、Cortex、Runtime。

## GitHub / Merge

- 可单独 merge。
- Commit message: `refactor(tools): quarantine audio qa tool`

