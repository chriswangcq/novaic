# NovAIC 文档索引

> **从这里开始**：先读 [**NOVAIC_CANONICAL_GUIDE.md**](NOVAIC_CANONICAL_GUIDE.md) — **单一入口**（分层阅读、防冗余、一表一图）；再按需下钻下列专章。  
> **树形视图**：[`TREE.md`](TREE.md) — `docs/` 物理目录树（脚本生成）+ DFS（L0→L3）阅读顺序说明。  
> 除下列 **必读** 与明确标注为「现行规范」的文档外，`docs/` 下大量内容为**过程稿、回合调研**，引用前请先看页眉说明。

---

## 必读（现行总览）

| 文档 | 用途 |
|------|------|
| [**NOVAIC_CANONICAL_GUIDE.md**](NOVAIC_CANONICAL_GUIDE.md) | **单一入口**：文档分层、拓扑、端口、数据归属、阅读顺序（**先读**） |
| [**TREE.md**](TREE.md) | **`docs/` 树形索引**：物理目录树 + L0–L3 DFS 顺序（`python3 docs/_scripts/generate_docs_tree.py` 重生成） |
| [backend-architecture.md](backend-architecture.md) | 后端组件、端口、数据归属、部署目录（详述） |
| [architecture-verification-2026-04.md](architecture-verification-2026-04.md) | 与代码/脚本对照的核查结论（配置缺口、deploy 差异等） |
| [agent-handoff-context.md](agent-handoff-context.md) | Gateway / Entangled / Cortex / Runtime 分工与协作习惯 |
| [../HANDOVER.md](../HANDOVER.md) | 仓库级交接：子模块、构建、部署命令（在仓库根） |

---

## 子系统（现行专章，与总览配合阅读）

| 主题 | 文档 |
|------|------|
| Cortex | [cortex-architecture.md](cortex-architecture.md) |
| Context / Scope | [context-assembly-dfs-step-tree.md](context-assembly-dfs-step-tree.md)、[scope-driven-agent-lifecycle.md](scope-driven-agent-lifecycle.md) |
| Entangled 协议 | [SYNC_CONTRACT.md](SYNC_CONTRACT.md)、[entangled-sync-protocol-v1.md](entangled-sync-protocol-v1.md)、[sync-contract-execution-checklist.md](sync-contract-execution-checklist.md) |
| 同步契约执行 | 同上 checklist |

---

## 目录约定

| 路径 | 定位 |
|------|------|
| [design/](design/) | 方案草案、迁移计划、历史设计（页眉多标「历史」类说明） |
| [device/](device/) | 设备域调研与回合报告 — [说明](device/README.md) |
| [research/](research/) | 调研、根因分析、回合报告 — [说明](research/README.md) |
| [runbooks/](runbooks/) | **现行运维**：E2E、服务矩阵、热更新步骤 — [索引](runbooks/README.md) |
| [misc/](misc/) | 杂项：调查、跨端笔记等 — [索引](misc/README.md) |
| [_legacy/](_legacy/) | L3 过程稿（design/research 等）角色说明 — [索引](_legacy/README.md) |
| [submodules/](submodules/) | 各子模块文档仅 **README**；父仓不保留镜像正文，详见 [submodules/README.md](submodules/README.md) |
| [gateway-upgrade/](gateway-upgrade/) | Gateway 瘦身/迁移 — [说明](gateway-upgrade/README.md)（过程稿） |
| [agent-approve-points/](agent-approve-points/) | 审核用条目（OpenClaw 对照、Runtime 要点等） |

---

## 运维与联调

- [runbooks/E2E_READINESS.md](runbooks/E2E_READINESS.md) — 本地启动顺序（现行栈）
- [runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md](runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md) — 服务与 Handler 矩阵
- [runbooks/HOT_UPDATE_DEPLOY_STEPS.md](runbooks/HOT_UPDATE_DEPLOY_STEPS.md) — 热更新部署步骤

---

## 归档与重建

- **原文档快照（推荐）**：在重大重组前打 **git tag**，见 [`_archive/README.md`](_archive/README.md)；可用 `docs/_scripts/snapshot_docs_manifest.sh` 生成本目录下 **`MANIFEST-*.txt`** 路径清单。
- **新文档体系构思**：见 [**NEW_DOCUMENTATION_BLUEPRINT.md**](NEW_DOCUMENTATION_BLUEPRINT.md)（信息架构、迁移顺序、成功标准与待决策项）。

## 激进整理策略（草案）

若需 **大规模删减、合并、外移归档**，见 [DOCUMENT_AGGRESSIVE_STRATEGY.md](DOCUMENT_AGGRESSIVE_STRATEGY.md)（分阶段动作、保留集、风险与门禁）。

**Hard purge（已执行）**：`docs/_graveyard/`、`docs/archived/` 已从工作树**删除**；若需曾迁入的旧副本，请用 **`git show docs-graveyard-p2:docs/_graveyard/...`** 或检出 tag **`docs-graveyard-p2`**。`docs/vnc/`、`docs/review/`、`docs/misc/survey-2026/` 仅保留 **README 占位**。

---

## 如何判读页眉

- **「过程稿 / 调研 / 镜像」**：非唯一权威，以 [NOVAIC_CANONICAL_GUIDE.md](NOVAIC_CANONICAL_GUIDE.md) 与必读表为准。
- **「现行规范 / 子系统 / 配套」**：可与 `backend-architecture.md` 交叉引用。
- 若正文仍出现已删除服务（如 RO `:19993`、必选 Tools Server），视为**历史段落**，以页眉与必读文档为准。

---

## 完整清单

- [DOCUMENT_INVENTORY.md](DOCUMENT_INVENTORY.md) — 全库 `.md` 路径表（按目录汇总 + 全路径列表）。
- [DOCUMENT_INVENTORY_ANNOTATED.md](DOCUMENT_INVENTORY_ANNOTATED.md) — **同上 + 每篇用途 / 是否符合现状 / 不可删除原因**（与 `DOCUMENT_INVENTORY.md` 同步自动生成；重生成：`python3 docs/_scripts/regen_document_inventory.py`）。
- **与代码分歧**：以 `architecture-verification-2026-04.md`、根 `HANDOVER.md` 与 **`scope-driven-agent-lifecycle.md` §〇（对照表）** 为先；长文设计稿务必逐条对 `novaic-gateway` / `novaic-agent-runtime` / `novaic-cortex`。
- **全量持疑核验（scale-up）**：[DOC_VERIFICATION_REGISTRY.md](DOC_VERIFICATION_REGISTRY.md) — 每文件状态；**[待检查总表 · 每批 8](PENDING_DOC_VERIFICATION.md)**（**已按优先级排序**：先 `HANDOVER` / `README` / `SYNC_CONTRACT` 与 checklist、再 `docs/` 根专章、再 `misc/`，**`design/` 过程稿在最后**，避免入口文档长期挂起）；模板 [`_scripts/SKEPTICAL_VERIFY_TEMPLATE.md`](_scripts/SKEPTICAL_VERIFY_TEMPLATE.md)；进度 JSON [`_scripts/verification_state.json`](_scripts/verification_state.json)。重生成登记 + 待办表：`python3 docs/_scripts/regen_verification_registry.py`。分批 CSV：`python3 docs/_scripts/emit_verify_batches.py`（默认每批 8）→ `docs/_verification/verify_batches.csv`。
