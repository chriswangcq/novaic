# Skills 领域分调查报告

> 调查基准日期：2026-04-02  
> 范围：NovAIC 仓库内 `novaic-gateway`、`novaic-app`、`novaic-agent-runtime`，以及参考子模块 `thirdparty/openclaw` 的 skills 实现。  
> 目的：按子领域独立成文，便于评审、立项与对外沟通。

---

## 调查报告一：技能发现与存储模型

### 1.1 调查背景

「技能」在 AI Agent 产品中既可表现为**文件**（如 `SKILL.md`），也可表现为**数据库记录**。发现顺序、合并规则与存储位置直接决定：多端一致性、可审计性与用户心智。

### 1.2 OpenClaw 现状（参考）

- **多根目录合并**：`extraDirs`（含插件目录）→ bundled → `~/.openclaw/skills` → `~/.agents/skills` → `<workspace>/.agents/skills` → `<workspace>/skills`；同名技能 **后写入覆盖**（Map merge）。
- **契约**：每技能目录含 `SKILL.md`，YAML frontmatter 至少含 `name`、`description`；路径经 `realpath` 等约束，降低目录穿越风险。
- **ClawHub**：通过安装流将技能包落到 workspace（如 `<workspace>/skills`），而非在 loader 内嵌远程目录列表。
- **依据代码路径**：`thirdparty/openclaw/src/agents/skills/workspace.ts`、`local-loader.ts`、`docs/tools/skills.md`。

### 1.3 NovAIC 现状

- **Builtin**：Gateway `SkillRepository` 从 **`gateway/mcp_client/skills/*/SKILL.md`** 扫描加载，合成 `builtin:<dir>` 等 id；只读，不可 update/delete。
- **Custom**：SQLite `skills` 表，Entangled 实体 `skills`，`user_id` 隔离；支持 fork（自 builtin 复制为可编辑副本）。
- **Agent 绑定**：`agent_skills` 表关联 agent 与 skill，带 `priority`。
- **用户工作区文件树**：桌面 App **不扫描**用户工程下的 `SKILL.md` 自动入库；与 OpenClaw「workspace/skills」模型不对齐。
- **依据代码路径**：`novaic-gateway/gateway/db/repositories/skill.py`、`gateway/entity/defs.py`（`SKILLS`）。

### 1.4 结论

| 维度 | OpenClaw | NovAIC |
|------|----------|--------|
| 事实来源 | 文件系统多根 + 明确优先级 | 服务端 DB + 固定目录 builtin |
| 多端同步 | 依赖本机/工作区布局 | Entangled 同步列表，一致性好 |
| 可扩展发现 | 强（插件目录、workspace） | 弱（无通用 workspace 扫描） |

### 1.5 建议（本领域）

1. 在产品/设计文档中**书面定义** NovAIC 的合并优先级（例如：per-agent 绑定 > 自动匹配 > 默认 builtin），避免与 OpenClaw 混用概念时产生误解。  
2. 若需「仓库内 SKILL.md」：单独立项 **导入器**（扫描 → 校验 → 写入 `skills` 实体或临时 session 附件），不宜静默与 DB 双写。

---

## 调查报告二：Prompt 注入与 Token 预算

### 2.1 调查背景

技能内容进入模型上下文的方式影响：**成本**、**上下文窗口占用**、以及**模型是否按需读取**长文本。

### 2.2 OpenClaw 现状（参考）

- 通过 `formatSkillsForPrompt` / 紧凑 XML 等形式注入；存在 **字符上限**、**技能条数上限**、单文件大小上限；超标时 **compact 模式**（保留名称与路径提示，引导模型后续自读）。
- **环境变量**：`applySkillEnvOverrides` 将技能相关 secrets 注入进程环境（含恢复与 refcount 设计），避免写进 prompt。
- **依据**：`thirdparty/openclaw/src/agents/skills/workspace.ts`、`env-overrides.ts`、`pi-embedded-runner/skills-runtime.ts` 与 `attempt.ts` 中的 `effectiveSkillsPrompt` 链路。

### 2.3 NovAIC 现状

- Runtime `system_prompt.py`：拉取 **已分配** + **自动匹配** 技能后 `_merge_skills`，再 **`_build_skills_section`** 将每个技能的 **description、prompt、workflow 全文**拼入固定标题「已加载的技能 (Domain Knowledge)」。
- **未见**：总字符数上限、技能数量截断、compact 目录模式。
- **依据**：`novaic-agent-runtime/task_queue/utils/system_prompt.py`（`_build_skills_section` 等）。

### 2.4 结论

NovAIC 当前策略对模型**最简单**（全量可见），但在技能数量或单技能 prompt 变长时，**易挤占 system 上下文**且无渐进降级。OpenClaw 在**规模化技能库**场景下更可控。

### 2.5 建议（本领域）

1. **短期**：在 `_build_skills_section` 或上游合并处增加 **硬上限**（例如总字符数、最多 N 个技能），超出时记录日志并截断或改为「仅标题+id+一行摘要」。  
2. **中期**：引入 **二级加载**（目录式摘要 + 由工具/检索拉取全文），需与工具列表与任务类型协同设计。  
3. **Secrets**：继续避免将密钥写入 skill 正文；与 OpenClaw 对齐时优先学 **环境/密钥侧注入**，而非全文进 prompt。

---

## 调查报告三：运行时匹配与 Agent 绑定

### 3.1 调查背景

「哪些技能进入本轮对话」由 **显式绑定** 与 **自动匹配** 共同决定；匹配质量影响相关性幻觉与 token 浪费。

### 3.2 NovAIC 现状

- **绑定**：`gateway_client.get_agent_skills(agent_id)` → 进入 merge。  
- **自动匹配**：`auto_match_skills` 为真且存在 `task` 时，`gateway_client.match_skills_for_task(task)`；仓库侧为 **关键词子串** 类逻辑（`SkillRepository.match_skills_for_task`），无匹配时可回落到默认 builtin（如文档所述 desktop）。  
- **前端**：`useSkills` 暴露 `matchForTask`，但 **业务 TSX 基本未调用**；与 Runtime 的 HTTP 路径并存，存在「UI 与运行时行为不一致」的认知成本。  
- **依据**：`system_prompt.py`、`novaic-gateway/gateway/db/repositories/skill.py`、`novaic-app` hooks 使用情况（grep）。

### 3.3 OpenClaw 现状（参考）

- 技能进入 run 与 **workspace 扫描快照**、**skillsSnapshot.prompt** 短路相关；与 **任务文本** 的「关键词 HTTP 匹配」不是同一套机制，更偏文件发现 + 配置 allowlist。  
- 直接对比时需注意：**OpenClaw 偏文件与配置驱动，NovAIC 偏服务端任务驱动**。

### 3.4 结论

NovAIC 的 **运行时路径清晰**（assigned + match → prompt），但 **匹配算法较朴素**；前端未充分暴露「为何本轮带上某技能」的可解释性。

### 3.5 建议（本领域）

1. 在 Debug/内部日志中输出 **本轮 skill id 列表及来源**（assigned / matched / fallback）。  
2. 评估升级匹配：**embedding 召回**、**任务类型标签**、或 **用户开关** 关闭 auto_match。  
3. 若保留 `match` 的 Entangled action：考虑在 **设置页或开发者模式** 暴露「预览本轮匹配结果」，与 Runtime 使用同一 API，消除双轨。

---

## 调查报告四：安装、分发与市场形态

### 4.1 调查背景

技能生态需要 **获取路径**（官方包、第三方市场、自建 Git）、**版本与签名**、以及 **租户策略**。

### 4.2 OpenClaw 现状（参考）

- **Gateway 方法**：`skills.status`、`skills.install`、`skills.update`（含 ClawHub 源）。  
- **UI**：技能列表、分组、安装入口，外链 **ClawHub** 浏览；应用内非完整内置商店浏览器。  
- **依据**：`thirdparty/openclaw/src/gateway/server-methods/skills.ts`、`ui/src/ui/views/skills.ts`。

### 4.3 NovAIC 现状

- **CRUD + Fork**：Settings `SkillsPage`、Entangled `skills` 实体、`fork` action；builtin 不可编辑，fork 后可改。  
- **市场 / 一键远程安装**：`HANDOVER.md` 技术债中仍为 **待办**（Skill 商店 / ClawHub 类集成）。  
- **无**：面向租户的签名包、审计链、依赖扫描的正式流程（若未来引入第三方包则必补）。

### 4.4 结论

NovAIC 当前是 **账户内技能资产管理** 成熟，**公共分发与发现**薄弱。OpenClaw 已形成 **「目录站 + 网关安装」** 的闭环雏形。

### 4.5 建议（本领域）

1. **Phase A**：文档化「从 Git/zip 导入技能」的运营流程（即使先做人工审核 + 手工入库）。  
2. **Phase B**：网关 **curated registry**（元数据 JSON + 签名或 checksum），客户端只装白名单源。  
3. **勿照搬**：无验证的任意 URL 安装，在 SaaS 场景下 **供应链风险过高**。

---

## 调查报告五：安全、合规与运维

### 5.1 调查背景

技能内容可能包含 **指令注入**、**敏感数据**、**恶意工作流**；运维需可观测、可回滚。

### 5.2 NovAIC 现状

- **权限**：自定义技能 **user_id** 隔离；builtin 不可篡改；fork 链可追溯 `forked_from`。  
- **HTTP API**：`skills.py` 对 builtin 的 update/delete 拒绝。  
- **内容侧**：未见自动 **SKILL.md 静态扫描**（脚本路径、危险命令模式）作为 CI 门禁；依赖产品与代码审查。  
- **Runtime**：技能全文进 system prompt，若数据被污染则影响面大，需在 **写入端**（DB/API）与 **可选运行时策略**（长度/关键词黑名单）双保险。

### 5.3 OpenClaw 现状（参考）

- 路径约束、文件大小、技能条数限制降低 DoS 与误配面；DM/通道侧有 **pairing/allowlist** 等与「技能」并列的安全叙事。  
- **全局 `process.env` 注入** 技能 secrets：便利但与多租户/子进程隔离需谨慎；NovAIC 若以 **进程级环境** 复刻需评估与 Queue Worker 多任务并发关系。

### 5.4 结论

NovAIC **访问控制**清晰；**内容安全与供应链**随「市场/导入」功能放大而需前置设计。OpenClaw 的 **限额与路径安全** 值得吸收为 **网关/Runtime 策略**，而非照搬 env 全局修改。

### 5.5 建议（本领域）

1. 对 **自定义 skill 的 prompt/workflow** 做 **长度与简单模式校验**（网关或 Factory 前）。  
2. 官方 builtin 目录 **CI 校验** SKILL frontmatter 与允许字段（可对齐 OpenClaw `quick_validate` 思路）。  
3. 企业客户场景预留 **组织级 skill 黑名单/仅允许内置** 开关。

---

## 附录：关键文件索引

| 系统 | 路径 |
|------|------|
| NovAIC Gateway 仓储与匹配 | `novaic-gateway/gateway/db/repositories/skill.py` |
| NovAIC skills 实体定义 | `novaic-gateway/gateway/entity/defs.py`（`SKILLS`） |
| NovAIC skill actions | `novaic-gateway/gateway/api/skill_actions.py` |
| NovAIC Runtime prompt | `novaic-agent-runtime/task_queue/utils/system_prompt.py` |
| NovAIC 前端技能页 | `novaic-app/src/components/Settings/SkillsPage.tsx` |
| OpenClaw 技能加载 | `thirdparty/openclaw/src/agents/skills/workspace.ts` |
| OpenClaw 文档 | `thirdparty/openclaw/docs/tools/skills.md` |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-04-02 | 初版：五个子领域独立调查报告 |
