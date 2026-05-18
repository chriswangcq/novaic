# T445 Result: Aggregate Compatibility Guard Matrix Rerun

## Summary

完成最终兼容/残留聚合扫描，并把扫描输出保存为可复查的指针文件。扫描命中已按 state/finalize/generation、context projection、media/payload、tests 四类归档；未发现未分类的高风险兼容分支或旧活路径。

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p453/source-state-guard.txt`：状态、generation、finalize、active-session、remaining-stack 相关源码命中矩阵，共 299 行。
- `.complex-problems/L20260516-222011/tmp/p453/source-compat-media-guard.txt`：context projection、tool-output、display/media、base64/blob 边界相关源码命中矩阵，共 76 行。
- `.complex-problems/L20260516-222011/tmp/p453/tests-compat-guard.txt`：兼容/残留/边界守卫测试命中矩阵，共 124 行。

## Classification

1. State/finalize/generation：
   - `missing_generation` 是 FSM 明确拒绝旧/缺失 generation 的 reason，不是兼容分支。
   - `expected_session_generation` 仍作为 attach/outbox 二次确认契约存在，是目标逻辑。
   - `finalize_reason` / `remaining_stack` 在 queue/session 边界被用于结构化 finalize ownership；相关命中不是旧分支。
   - `cortex_handlers.py` 中 `finalize_reason = payload.get("finalize_reason", "stack_empty")` 仅在 runtime structural `scope_end` 路径完成 generation / remaining_stack 校验后进入归档诊断；已由后续 focused tests 覆盖，不在本票据中改动。

2. Context projection：
   - `/v1/context/read|append|batch` 是 materialized projection 的桥接/测试入口。
   - `/v1/context/prepare_for_llm` 是 LLM context prepare 权威路径。
   - `read_materialized_context_projection` / `append_materialized_context_projection*` 命名已将旧 `read_context` / `append_context` 语义收紧。

3. Media/payload：
   - `tool-output.v1` manifest 是 shell 输出契约目标状态。
   - base64 命中保留在 device/blob/provider/display perception 的边界内；历史 tool 输出不能再把图片 base64 当文本塞回 LLM context。
   - display current-turn visual input 是显式感知路径；history projection 只保留 manifest/pointer。

4. Tests：
   - test 命中主要是 negative guard、legacy residue guard、fixture contract、focused behavior tests。
   - 未发现未分类的高风险兼容分支或旧活路径。

## Changes

本 ticket 只做聚合扫描和分类，不做源码改动。

## Residual Risk

仍需用 P454 的 focused behavior test rerun 确认这些分类对应的活路径行为没有回归。
