#!/usr/bin/env python3
"""Regenerate DOCUMENT_INVENTORY.md and DOCUMENT_INVENTORY_ANNOTATED.md from current tree."""
from __future__ import annotations

import os
from pathlib import Path


DOCS = Path(__file__).resolve().parents[1]


def rel_docs(p: Path) -> str:
    return str(p.relative_to(DOCS.parent)).replace("\\", "/")


def top_bucket(rel: str) -> str:
    # rel like "docs/foo/bar.md"
    parts = rel.split("/")
    if len(parts) <= 2:
        return "(根目录)/"
    return parts[1] + "/"


DIR_LABELS: dict[str, str] = {
    "design/": "产品/网关/P2P/Tauri 等方案与迁移计划",
    "misc/": "联调、运维、调查汇总",
    "runbooks/": "现行运维（E2E、服务矩阵、热更新）",
    "_legacy/": "L3 档案角色说明（索引页）",
    "research/": "根因分析、历史栈调研、回合报告",
    "device/": "设备管理、PC Client、多轮调查",
    "ota/": "OTA 热更新与前端审查",
    "p2p/": "P2P / Relay / 重构提案与审查",
    "submodules/": "各子模块：仅 README",
    "gateway-upgrade/": "Gateway 瘦身与路由拆分系列（过程稿）",
    "agent-approve-points/": "Agent 审核点（Runtime / OpenClaw / 优化）",
    "sync_design/": "多端同步与本地缓存（现行说明）",
    "icons/": "图标资源说明",
    "vnc/": "占位：历史正文仅 git tag",
    "review/": "占位：历史正文仅 git tag",
}


def bucket_label(bucket: str) -> str:
    if bucket == "(根目录)/":
        return "总览、协议、Entangled/Cortex 专章、索引等"
    return DIR_LABELS.get(bucket, "文档")


def annotate(rel: str) -> tuple[str, str, str]:
    """Return (用途, 是否符合现状, 不可删除原因)."""
    p = rel
    name = Path(p).name

    if p == "docs/DOCUMENT_AGGRESSIVE_STRATEGY.md":
        return ("激进文档整理策略（草案）", "是", "分阶段删并/外移门禁")
    if p == "docs/DOCUMENT_INVENTORY.md":
        return ("全路径文件清单（自动生成）", "是", "检索用；可重生成但建议保留")
    if p == "docs/DOCUMENT_INVENTORY_ANNOTATED.md":
        return ("本表：用途/现状/保留理由（自动生成）", "是", "元索引；可重生成")
    if p == "docs/NOVAIC_CANONICAL_GUIDE.md":
        return ("单一入口权威指南", "是", "分层阅读与防冗余；摘要不替代 L1 专章")
    if p == "docs/README.md":
        return ("文档总索引与必读链接", "是", "入口页；删除后协作者失去导航")
    if p == "docs/TREE.md":
        return ("docs 物理目录树与 DFS（L0–L3）说明", "是", "树形导航；`generate_docs_tree.py` 重生成")
    if p == "docs/DOC_VERIFICATION_REGISTRY.md":
        return ("全库文档持疑核验登记", "是", "`regen_verification_registry.py` 重生成；进度在 `verification_state.json`")
    if p == "docs/PENDING_DOC_VERIFICATION.md":
        return ("待检查文件分批总表", "是", "与 `verification_state.json` 同步；同脚本重生成")

    if p == "docs/vnc/README.md":
        return ("VNC 目录占位", "是", "历史仅 git tag；指向 SSOT")
    if p == "docs/review/README.md":
        return ("review 目录占位", "是", "历史仅 git tag")
    if p == "docs/misc/survey-2026/README.md":
        return ("survey-2026 占位", "是", "历史仅 git tag")
    if p == "docs/misc/README.md":
        return ("misc 目录索引", "是", "联调/运维入口表")
    if p == "docs/NEW_DOCUMENTATION_BLUEPRINT.md":
        return ("新文档体系重建蓝图（草案）", "部分", "规划用；定稿后与 Canonical 对齐")
    if p == "docs/_archive/README.md":
        return ("文档归档说明（git tag + 清单）", "是", "快照与取回方式")
    if p == "docs/_legacy/README.md":
        return ("L3 档案区说明（索引）", "是", "design/research 等角色；不替代 SSOT")
    if p.startswith("docs/runbooks/"):
        return ("运维 Runbook", "部分", "联调与部署；以 backend-architecture 为准")

    if p.startswith("docs/design/"):
        return ("设计与迁移方案", "部分", "对照代码与现行架构验证")
    if p == "docs/research/README.md":
        return ("research 目录说明", "是", "声明时点稿性质；指向 SSOT")
    if p.startswith("docs/research/"):
        return ("调研与根因分析", "部分", "历史上下文；删则难追溯决策")
    if p == "docs/device/README.md":
        return ("device 目录说明", "是", "声明调研稿性质；指向 SSOT")
    if p.startswith("docs/device/"):
        return ("设备域文档", "部分", "产品/实现对照材料")
    if p.startswith("docs/ota/"):
        return ("OTA 与热更新", "部分", "实现与审查记录")
    if p.startswith("docs/p2p/"):
        return ("P2P / Relay", "部分", "协议与实现迭代记录")
    if p == "docs/misc/CLIENT_DB_ARCHITECTURE.md":
        return ("端上数据与缓存（现行）", "是", "与 sync_design、backend-architecture 配套")
    if p == "docs/misc/CROSS_PLATFORM_ARCHITECTURE.md":
        return ("跨平台架构分析", "部分", "抽象建议；存储与同步以 sync_design 为准")
    if p.startswith("docs/misc/"):
        return ("杂项与联调", "部分", "运维与协作记录")
    if p.startswith("docs/submodules/"):
        return ("子模块索引", "是", "指向各子仓；父仓不保留镜像")
    if p == "docs/gateway-upgrade/README.md":
        return ("gateway-upgrade 目录说明", "是", "声明过程稿；指向 SSOT")
    if p.startswith("docs/gateway-upgrade/"):
        return ("Gateway 升级系列", "部分", "演进与拆分记录")
    if p.startswith("docs/agent-approve-points/"):
        return ("Agent 审核点", "部分", "规范与检查清单")
    if p.startswith("docs/sync_design/"):
        return ("同步与缓存实现说明", "是", "与 Sync Contract、novaic-app 对照")
    if p.startswith("docs/icons/"):
        return ("图标资源", "是", "资源说明")

    if p == "docs/SYNC_CONTRACT.md":
        return ("Sync Contract v0.1", "是", "协议级规范")

    # Root-level architecture / handoff style
    stem = name.lower()
    if any(
        x in stem
        for x in (
            "architecture",
            "handover",
            "verification",
            "backend",
            "frontend",
            "entangled",
            "cortex",
        )
    ):
        return ("架构/验证/专章", "部分", "总览与对照代码；核心导航材料")

    return ("docs 根目录文档", "部分", "索引、协议或协作说明")


def sort_paths(paths: list[str]) -> list[str]:
    return sorted(paths, key=lambda p: p.lower())


def main() -> None:
    md_files = list(DOCS.rglob("*.md"))
    paths = sort_paths([rel_docs(p) for p in md_files])

    from collections import Counter

    buckets = Counter(top_bucket(p) for p in paths)

    # inventory md
    lines_inv: list[str] = [
        "# docs 文档清单（自动生成）",
        "",
        f"> 共 **{len(paths)}** 个 `.md` 文件。路径相对于仓库根。",
        "",
        "## 按目录汇总",
        "",
        "| 目录 | 文件数 | 标注 |",
        "|------|--------:|------|",
    ]

    # sort buckets: root first, then alpha, _graveyard last or first - match old style: by count desc
    bucket_order = sorted(buckets.keys(), key=lambda b: (-buckets[b], b))
    for b in bucket_order:
        label = bucket_label(b)
        lines_inv.append(f"| `{b}` | {buckets[b]} | {label} |")

    lines_inv.extend(["", "## 完整列表", "", "| 路径 | 目录 | 标注 |", "|------|------|------|"])
    for p in paths:
        b = top_bucket(p)
        lines_inv.append(f"| `{p}` | `{b}` | {bucket_label(b)} |")

    inv_path = DOCS / "DOCUMENT_INVENTORY.md"
    inv_path.write_text("\n".join(lines_inv) + "\n", encoding="utf-8")

    # annotated
    lines_ann: list[str] = [
        "# docs 文档注解清单（自动生成）",
        "",
        "> 列：路径 · 用途 · 是否符合现状 · 不可删除原因（或保留价值）。",
        "> 「是否符合现状」：是 = 与当前主线一致或仍作规范；部分 = 时点/领域稿需对照代码；否 = 归档区刻意保留的历史。",
        "",
        "| 路径 | 用途 | 是否符合现状 | 不可删除原因 |",
        "|------|------|-------------|-------------|",
    ]
    for p in paths:
        u, c, r = annotate(p)
        lines_ann.append(f"| `{p}` | {u} | {c} | {r} |")

    ann_path = DOCS / "DOCUMENT_INVENTORY_ANNOTATED.md"
    ann_path.write_text("\n".join(lines_ann) + "\n", encoding="utf-8")

    print(f"Wrote {len(paths)} rows -> {inv_path.name}, {ann_path.name}")


if __name__ == "__main__":
    main()
