# 激进文档整理策略（草案）

> 目标：在 **不牺牲现行权威与合规证据** 的前提下，最大限度 **压缩体积、降低检索噪音、消灭重复与僵尸文档**。  
> 本文是 **策略与门禁**，执行前需负责人确认；删除类操作优先在 **独立分支 + PR** 中进行。

---

## 一、原则

| 原则 | 说明 |
|------|------|
| **单一事实来源（SSOT）** | 后端拓扑与部署真相只认：`backend-architecture.md` + `architecture-verification-2026-04.md` + 根 `HANDOVER.md`；其余一律降级为「补充」或删除。 |
| **先归档再删** | 除明确垃圾外，大批量删除前先 **打 git tag**（如 `docs-snapshot-before-purge-YYYY-MM-DD`）或整目录 `git mv` 到临时归档目录，合并后再择机物理删除。 |
| **按目录定生死** | 不同目录风险不同；**最激进**的是合并重复主题的 **survey/round** 与 **phase 审查**。 |
| **镜像服从子仓** | `docs/submodules/**` 非权威：激进策略下 **只保留各子目录 README**，正文一律不保留于父仓，强制读者去子模块仓库读。 |

---

## 二、保留集（不可动，除非改写迁移）

以下 **删除前必须迁移链接** 到 `docs/README.md` 与 handoff：

- `docs/NOVAIC_CANONICAL_GUIDE.md`（单一入口；摘要层）
- [`TREE.md`](TREE.md)（物理目录树 + DFS 说明；可脚本重生成，**入口与保留集语义不变**）
- [`DOC_VERIFICATION_REGISTRY.md`](DOC_VERIFICATION_REGISTRY.md) + `docs/_scripts/verification_state.json`（持疑核验总表与进度；可重生成，**删前需有替代登记**）
- [`PENDING_DOC_VERIFICATION.md`](PENDING_DOC_VERIFICATION.md)（分批派单总表；与 `verification_state.json` 配套）
- `docs/README.md`
- `docs/backend-architecture.md`
- `docs/architecture-verification-2026-04.md`
- `docs/agent-handoff-context.md`
- `docs/cortex-architecture.md`
- `docs/context-assembly-dfs-step-tree.md`
- `docs/scope-driven-agent-lifecycle.md`
- `docs/SYNC_CONTRACT.md` + `docs/sync-contract-execution-checklist.md`
- `docs/entangled-sync-protocol-v1.md`
- `docs/entangled-params-canonical.md` / `docs/entangled-pk-conventions.md`（若仍被实现引用；文件在 `docs/`）
- 根 `HANDOVER.md`（不在 `docs/` 但属 SSOT）

---

## 三、激进动作矩阵（按目录）

| 目录 | 激进动作 | 风险 | 缓解 |
|------|----------|------|------|
| **`docs/vnc/`** | 仅 README 占位；正文不保留于父仓 | 丢历史 bug 细节 | **purge 前 tag**；`git show tag:...` |
| **`docs/review/`** | 同上 | 审计/责任链断裂 | 同上；或 PDF 外存 |
| **`docs/research/`** | RO/Tools 类等按主题合并或删 | 丢调研细节 | tag；综述列原路径@commit |
| **`docs/design/`** | 已落地且不符代码的删或一句指向代码 | 丢未采纳方案 | 链接到旧 commit |
| **`docs/misc/`** | 合并运维稿；过时 VPN 等删或移 wiki | 丢运维细节 | 仅保留现行 runbook |
| **`docs/p2p/`、`docs/ota/`、`docs/device/`** | 每目录少量现行 + README | 中 | 同上 |
| **`docs/submodules/**`** | **仅各目录 `README.md`** | 父仓离线不可读 | README 写子模块仓库 URL |
| **`docs/gateway-upgrade/`** | 可合并为单篇 SUMMARY | 中 | 摘要列原 commit |

*（历史：曾将 vnc/review/survey-2026/子模块镜像等迁入 `docs/_graveyard/`；**已在 hard purge 中从工作树删除**，仅 tag 中可检出。）*

---

## 四、分阶段执行（建议）

| 阶段 | 内容 | 产出 |
|------|------|------|
| **P0** | Tag；删明显重复/空文件 | PR「docs: remove orphans」 |
| **P1** | 子模块仅 README；调研批量迁出或删 | PR「docs: submodule trim」 |
| **P2** | vnc/review/survey 迁出父仓 | PR「docs: archive copies」 |
| **P3** | design 深度合并；可选物理删归档目录 | 需负责人确认 |

---

## 五、门禁与自动化

1. **CI（可选）**：`main` 上 `docs/**/*.md` 行数总和 **环比下降超过 X%** 时只告警不阻断；**新增** `docs/` 下文件需经过 `CODEOWNERS`。
2. **脚本**：仓库根执行 **`./scripts/docs-count.sh`** — 按 `docs/` 第一级目录统计 `.md` 篇数。全量路径表重生成：**`python3 docs/_scripts/regen_document_inventory.py`**。
3. **禁止**：无 tag / 无 PR 直接在 `main` 上大批量 `rm -rf docs/` 子树。

---

## 六、成功指标（激进版）

- `docs/**/*.md` **总篇数**持续下降；**根目录**（除 SSOT 与协议）保持精简。
- **读者路径**：新人只读 `README.md` → SSOT → 子系统专章。

---

## 七、回滚

- 任意阶段：**`git revert`** 或 **`git checkout <tag> -- docs/`**。
- **已删目录**（如曾有的 `docs/_graveyard/`）：从 **`docs-graveyard-p2`** 等 tag 恢复：`git checkout docs-graveyard-p2 -- docs/_graveyard`。

---

## 八、与当前仓库状态的关系

- **Hard purge（已执行）**：`docs/_graveyard/`、`docs/archived/` 已从工作树**物理删除**；历史副本仅存在于 **git tag**（如 **`docs-graveyard-p2`**、**`docs-graveyard-p1`**）或旧提交。
- **占位保留**：`docs/vnc/README.md`、`docs/review/README.md`、`docs/misc/survey-2026/README.md` — 说明如何 **`git show`** 取回旧文。
- **自动化**：`./scripts/docs-count.sh`、`python3 docs/_scripts/regen_document_inventory.py`（见 §五）。
- **未执行（可选）**：`misc/` 合并为单篇 `CURRENT_GAPS.md`；`design/`/`research/` 深度合并；**VNC/审查「现行结论」合成单页**。
