#!/usr/bin/env python3
"""Generate docs/TREE.md — physical tree + DFS layer map. Run from repo root: python3 docs/_scripts/generate_docs_tree.py"""
from __future__ import annotations

from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
REPO = DOCS.parent


def tree_lines(root: Path, prefix: str = "") -> list[str]:
    out: list[str] = []
    try:
        raw = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return out
    entries = [p for p in raw if not (p.name.startswith(".") and p.name != ".gitkeep")]
    for i, p in enumerate(entries):
        is_last = i == len(entries) - 1
        branch = "└── " if is_last else "├── "
        if p.is_dir():
            out.append(f"{prefix}{branch}{p.name}/")
            ext = "    " if is_last else "│   "
            out.extend(tree_lines(p, prefix + ext))
        else:
            out.append(f"{prefix}{branch}{p.name}")
    return out


def main() -> None:
    lines: list[str] = [
        "# docs/ 树形索引（自动生成 + DFS 说明）",
        "",
        "> **物理结构**：下列 `docs/` 目录树由脚本扫描生成，反映仓库内真实路径。",
        "> **重生成**：在仓库根执行 `python3 docs/_scripts/generate_docs_tree.py`。",
        "",
        "---",
        "",
        "## 1. DFS 阅读顺序（从总入口到最底层）",
        "",
        "逻辑层级与 [`NOVAIC_CANONICAL_GUIDE.md`](NOVAIC_CANONICAL_GUIDE.md) 一致：",
        "",
        "```",
        "L0  入口",
        " ├─ NOVAIC_CANONICAL_GUIDE.md",
        " └─ README.md",
        "L1  现行总览（与代码/运维对齐）",
        " ├─ backend-architecture.md",
        " ├─ architecture-verification-2026-04.md",
        " ├─ agent-handoff-context.md",
        " └─ ../HANDOVER.md（仓库根）",
        "L2  子系统专章（深入单域）",
        " ├─ cortex-architecture.md / context-assembly-dfs-step-tree.md / scope-driven-agent-lifecycle.md",
        " ├─ SYNC_CONTRACT.md / entangled-sync-protocol-v1.md / sync-contract-execution-checklist.md",
        " └─ …（见 Canonical §10 表）",
        "L3  过程稿（最底层叶子：按主题目录展开）",
        " ├─ design/          — 方案与迁移草案",
        " ├─ research/       — 调研与根因",
        " ├─ device/         — 设备域回合",
        " ├─ gateway-upgrade/ — Gateway 拆分过程",
        " ├─ ota/ / p2p/     — 专题记录",
        " ├─ misc/           — 联调运维",
        " └─ …（见下方物理树）",
        "```",
        "",
        "**DFS 到最底层**：在某一 L3 目录内，按文件名或时间自行深读；**不要求**读完所有 `.md`，以页眉「过程稿/调研」为准。",
        "",
        "---",
        "",
        "## 2. `docs/` 物理目录树（相对 `docs/`）",
        "",
        "```",
        "docs/",
    ]

    for line in tree_lines(DOCS):
        lines.append(line)

    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. 与分层对应关系（速查）")
    lines.append("")
    lines.append("| 物理路径 | 逻辑层 |")
    lines.append("|----------|--------|")
    lines.append("| 根下 `NOVAIC_CANONICAL_GUIDE.md`、`README.md`、`*architecture*`、`SYNC*` 等 | L0–L2 |")
    lines.append("| `design/`、`research/`、`device/`、`gateway-upgrade/`、`ota/`、`p2p/`、`agent-approve-points/` | L3 |")
    lines.append("| `runbooks/` | 现行运维（E2E、服务矩阵、热更新） |")
    lines.append("| `misc/` | 联调杂项与调查（核心 Runbook 在 `runbooks/`） |")
    lines.append("| `_legacy/` | L3 档案角色说明（索引；正文仍在各主题目录） |")
    lines.append("| `submodules/`、`vnc/`、`review/`、`icons/` | 占位或索引为主 |")
    lines.append("| `sync_design/` | 多端同步与缓存（现行说明，与 SYNC_CONTRACT 配套） |")
    lines.append("")

    out_path = DOCS / "TREE.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
