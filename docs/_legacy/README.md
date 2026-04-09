# 档案区说明（L3 过程稿入口）

本目录**不放正文**，只说明 **`docs/` 下大量 L3 内容的角色**：

| 路径 | 角色 |
|------|------|
| `design/` | 方案与迁移草案；**非**唯一真值 |
| `research/` | 调研与根因；时点记录 |
| `device/` | 设备域回合稿 |
| `gateway-upgrade/` | Gateway 拆分过程记录 |
| `ota/`、`p2p/` | 专题过程稿与修复记录 |
| `misc/` | 除已迁入 **`runbooks/`** 外的联调笔记、调查汇总等 |

**现行真相（L1）**：`backend-architecture.md`、`architecture-verification-2026-04.md`、根目录 `HANDOVER.md`。

物理上**未**把 `design/` 等整目录移入 `_legacy/`（避免一次性破坏数千处链接）；重建采用 **入口分层 + Runbook 抽出** 的渐进策略，见 **`../NEW_DOCUMENTATION_BLUEPRINT.md`**。
