# 新文档体系 — 重建蓝图（草案）

> **状态**：构思稿；与 **`NOVAIC_CANONICAL_GUIDE.md`**、**`README.md`** 并列，用于**规划**；定稿前不替代 SSOT。  
> **原文档快照**：打 tag 方式见 **`_archive/README.md`**。

---

## 1. 为什么要重建

| 问题 | 目标 |
|------|------|
| 篇数多、层级杂（design/research/device 混放） | **读者路径极短**：入口 → 现行真相 → 可选深读 |
| 与代码对齐成本高 | **契约型文档**（协议、端口、Sync Contract）与代码变更**同 PR 或同里程碑**更新 |
| 历史过程稿仍有价值 | **归档可读**（tag / 子路径），**正文不冒充现行** |

---

## 2. 建议的信息架构（新）

沿用并强化 **L0 → L1 → L2 → L3**（见 Canonical Guide），但**物理目录**可收紧为：

| 层 | 建议内容 | 读者 |
|----|-----------|------|
| **L0** | 单一入口 + `TREE` + 本蓝图链接 | 所有人 |
| **L1 现行** | `backend-architecture`、`architecture-verification-*`、`HANDOVER`（根）、`agent-handoff-context` | 开发/运维 |
| **L2 子系统** | Cortex、Entangled/Sync、Gateway 行为摘要（短） | 特性负责人 |
| **L3 档案** | 调研、回合、未采纳方案 | 考古/立项 |

**原则**：L1 **只保留可证伪、可对代码**的陈述；L3 **默认页眉标明时点/非 SSOT**。

可选物理调整（需单独 PR）：

- **（已执行 · Phase 1）** `docs/runbooks/`：已从 `misc/` 迁入 **E2E_READINESS**、**ARCHITECTURE-SERVICES-AND-HANDLERS**、**HOT_UPDATE_DEPLOY_STEPS**；索引见 `runbooks/README.md`。
- `docs/_legacy/`：仅 **`README.md`** 说明 `design/`、`research/` 等 L3 角色（正文未整体搬迁）。
- `docs/archive/` 或继续仅用 **git tag** 引用旧树，避免 `design/` 下大量文件与「现行」混读。

---

## 3. 重建顺序（建议）

1. **冻结快照**：`git tag -a docs-archive-…`（见 `_archive/README.md`）。
2. **定 L1 清单**：哪些留在 `docs/` 根、哪些只保留链接到子模块 README。
3. **搬移而非删除**：L3 大块先 `git mv` 到 `docs/research/` 或 `docs/_legacy/`（若采用），**链接批量替换**（脚本或半自动）。
4. **入口重写**：`README.md` + `NOVAIC_CANONICAL_GUIDE.md` 只指向新结构。
5. **门禁**：合并前 checklist — Sync Contract / 端口表 / `nav.rs` 是否与本次代码变更同步（与 `sync-contract-execution-checklist` 一致精神）。

---

## 4. 与自动化工具的配合

| 工具 | 用途 |
|------|------|
| `docs/_scripts/regen_document_inventory.py` | 全路径表；重建后重跑 |
| `docs/_scripts/regen_verification_registry.py` | 核验状态；**优先级队列**已按入口/契约优先 |
| `merge_verification_state.py` | 每篇文档登记 `verified` / `partial` |

重建后建议：**新 L1 页默认一次 `verified`**；L3 可标 `skipped` 或 `partial`（仅索引用途）。

---

## 5. 成功标准（可量化）

- 新人 **10 分钟内**能答：网关端口、Entangled 与 AppBridge 分工、文档 SSOT 是哪三篇。
- `docs/` 根目录 **现行专章**篇数可控（具体上限由负责人定）。
- 与代码冲突时，**以 verification + 子模块源码为准**，并**回写文档**而非长期搁置。

---

## 6. 待决策（负责人填）

- [x] **物理目录 `docs/_legacy/`**：已建 **`_legacy/README.md`**（索引说明；未搬移 `design/` 正文）。
- [x] **`design/` 策略（已定）**：**整目录保持为 L3 过程稿**（不强制合并为 ADR）；与 L1 冲突时以 **`architecture-verification`** + 代码为准；若将来要合并 ADR，单独立项。
- [x] **PR 模板**：父仓 **`.github/pull_request_template.md`** 已含「文档与契约」勾选（协议 / 端口 / Sync Contract）。

---

## 7. 相关链接

- [`_archive/README.md`](_archive/README.md) — 归档 tag 用法  
- [`DOCUMENT_AGGRESSIVE_STRATEGY.md`](DOCUMENT_AGGRESSIVE_STRATEGY.md) — 激进整理与风险  
- [`sync_design/multi_device_sync_caching.md`](sync_design/multi_device_sync_caching.md) — 客户端现行示例  
