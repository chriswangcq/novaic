# Cortex 设计文档 vs 实现 — Gap 汇总

**设计来源:** `docs/novaic_cortex_design.md`  
**实现来源:** `novaic-cortex/novaic_cortex/`  
**审计方式:** 8 路并行只读对照（2026-04-03）

---

## 2026-04-03 闭合记录（实现 + 文档）

以下项已由代码与/或设计文档、`CONTRACTS.md` 对齐：

| 原 Gap | 处理 |
|--------|------|
| §11 沙箱 / 仅 archive 写 scopes | 设计 §11 改为诚实描述主机 shell；补充 `__fused__` 系统写入 |
| §5 / §6 工具表 | §5 增补真实 façade；§6 JSON 增加 `create_scope`；`TOOL_SCHEMAS` + `tool_create_scope` |
| `files_changed` 不含删除 | `Sandbox` diff 含删除路径；`CONTRACTS` 已更新 |
| Compaction meta files/tools | JSONL 解析写入 `compaction` 与顶层 `files`/`tools` |
| `gem_fusion_max_level` > 2 | 通用 L1…LN fusion；按「已存在 fuse 节点数」去重，避免同一子集重复融合 |
| Recall `constraints.md` | `_config_section` 纳入 `constraints.md` |
| `micro_max_tool_output_chars` | `tool_read` 超长截断 |
| `sandbox_timeout_default` | `tool_shell` 默认超时读取 config |
| `max_skill_depth` | `install_skill` 按路径段数校验 |
| `on_skill_loaded` | 与 workspace 一致：async/sync + `UserWarning` |
| §12 日志字段 | `sandbox.exec` 增加 `exit`/`duration_s`；`scope.archived` 增加 `summary_len`/`messages`/`duration_s` |
| §8 scratch | `create_scope` 创建 `scratch/.keep` |
| Store 后端差异 | `CONTRACTS` 简述 delimiter / `move_prefix` |

**仍为产品级限制（非笔误）：** 沙箱不提供内核级隔离；`micro_preserve_recent` 保留给宿主消息管线（见 `CONTRACTS`）。

---

## 二次审计（再派 8 路只读 subagent，gap 复查）

**结论：** 大块功能已与设计/`CONTRACTS` 对齐；**剩余主要是文档精度与测试覆盖**，而非缺失实现。

| # | 范围 | 仍存在的 gap（摘要） |
|---|------|----------------------|
| 1 | §1–4.1 Store | §4.1 未写：`delimiter` 仅 `/`、`move_prefix` 跨后端计数语义、S3 可选依赖、并发说明 —— 以 `CONTRACTS` 为准即可。 |
| 2 | §4.2 / §11 | 隔离表述：真正绑 `agents/{id}/` 的是 `_key` 路径，而非 `CortexStore` 抽象本身；`runtime` 前缀校验弱于 `_key` —— 宜在设计中写清两层模型；工具拒绝裸 `/ro` vs `list_dir("/ro")` 轻微不一致。 |
| 3 | §4.3 Sandbox | `files_changed` 删除路径有单元测 `_logical_rw_changes`，**缺** shell `rm` 端到端测；§4.3 内未强调「仍是主机 shell」；日志里 `exit` 与 `exit_code` 重复。 |
| 4 | §4.4–4.5 Compactor | §4.4 **步骤 6「Update Recall」**：实现上无对 `Recall` 的调用，靠 `archive_scope` 更新索引；§4.4 `Compactor.__init__` 代码块过简；**fusion** 实为子 summary 拼接而非额外 LLM 摘要 —— 宜在 §4.5 写明。 |
| 5 | §4.6 / §5 | §4.6 伪代码 `filter(None)` 与正文「三节恒在」并存；§5 内嵌代码块过时（`tool_shell` 签名、`compact(report)` 等）；`CONTRACTS` 对坏 `engine.json` 宜补充 **`JSONDecodeError`**。 |
| 6 | §6–8 | 五工具与 schema 一致；§7 未单独写 `install_skill`（在 §5）；§8 流程图把注入写成一步，实际由宿主编排；`report` schema 必填 vs Python 默认 `""`。 |
| 7 | §9 Config | 包内仍**未读**字段：**仅 `micro_preserve_recent`**（与 `CONTRACTS`「保留给宿主」一致）。 |
| 8 | §10–12 / §14 | §12 指标块缺 **`skills_installed` / `compactions_completed`**；§14 包结构/导出严重落后于仓库；`hooks.py` 可补一行指向 §10.3 的签名说明；`scope.created` 多打 `name=`。 |

---

## 历史：执行摘要（审计当日）

- **对齐较好的部分:** `CortexStore` 能力集（§4.1）、Workspace 的 `/ro`/`/rw` ACL 与 `_key` 映射（§4.2）、四工具名与 `TOOL_SCHEMAS`（§6）、压缩主路径与 gem fusion、Recall 对 scopes/skills 索引的注入（§4.6 核心）、`Summarizer`/`TokenCounter` 协议形状（§10.2）。
- **当时文档需更新之处:** §11「仅 `archive_scope` 写 `/ro/scopes/`」与 **fusion** 矛盾；§5 公面 API 落后；§12 日志字段与实现不一致。
- **当时实现缺口:** 见上表「闭合记录」；跨后端 `move_prefix` 语义等见 `CONTRACTS`。

---

*本文件由设计对照审计生成；契约细节以 `novaic-cortex/CONTRACTS.md` 为准。*
