#!/usr/bin/env python3
"""Generate docs/DOC_VERIFICATION_REGISTRY.md + optional batch index for skeptical doc/code review.

State file: docs/_scripts/verification_state.json
Run from repo root: python3 docs/_scripts/regen_verification_registry.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
STATE_PATH = Path(__file__).resolve().parent / "verification_state.json"
OUT_PATH = DOCS / "DOC_VERIFICATION_REGISTRY.md"
PENDING_TABLE_PATH = DOCS / "PENDING_DOC_VERIFICATION.md"

# Paths excluded from "pending" work queue (still listed in full registry)
GENERATED_NAMES = frozenset(
    {
        "DOCUMENT_INVENTORY.md",
        "DOCUMENT_INVENTORY_ANNOTATED.md",
        "TREE.md",
        "DOC_VERIFICATION_REGISTRY.md",
        "PENDING_DOC_VERIFICATION.md",
    }
)

# Default subagent batch size (must match emit_verify_batches / 派单表)
BATCH_SIZE = 8


def classify_tier(rel: str) -> str:
    p = rel.replace("\\", "/")
    if p == "HANDOVER.md":
        return "仓库根 · SSOT"
    if p in ("docs/README.md", "docs/NOVAIC_CANONICAL_GUIDE.md"):
        return "L0 入口"
    if p.startswith("docs/submodules/"):
        return "子模块 README"
    if "/design/" in p or p.startswith("docs/design/"):
        return "L3 design"
    if "/research/" in p or p.startswith("docs/research/"):
        return "L3 research"
    if "/device/" in p or p.startswith("docs/device/"):
        return "L3 device"
    if "/ota/" in p or p.startswith("docs/ota/"):
        return "L3 ota"
    if "/p2p/" in p or p.startswith("docs/p2p/"):
        return "L3 p2p"
    if "/gateway-upgrade/" in p or p.startswith("docs/gateway-upgrade/"):
        return "L3 gateway-upgrade"
    if p.startswith("docs/runbooks/"):
        return "L1 runbooks"
    if p.startswith("docs/_legacy/"):
        return "L3 index"
    if "/misc/" in p or p.startswith("docs/misc/"):
        return "L2/L3 misc"
    if p.startswith("docs/agent-approve-points/"):
        return "L2 审核"
    if p.startswith("docs/_scripts/"):
        return "_scripts"
    stem = Path(p).name
    if stem in GENERATED_NAMES and p.startswith("docs/"):
        return "generated"
    if p.startswith("docs/") and p.count("/") == 1:
        return "docs 根"
    return "其他"


def load_state() -> dict:
    if not STATE_PATH.is_file():
        return {}
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if k != "_meta" and not k.startswith("_")}


def is_work_pending(rel: str, state: dict) -> bool:
    """True = 仍需派出 subagent 核对（非 generated/verified/skipped）。"""
    st = state.get(rel, {}).get("status", "pending")
    if st in ("verified", "generated", "skipped"):
        return False
    # partial / stale / pending → 仍进待办总表（可重派）
    name = Path(rel).name
    if name in GENERATED_NAMES and rel.startswith("docs/"):
        return False
    # 工作流脚本与模板：不进「待派出核对」队列（改模板即改流程本身）
    if rel.startswith("docs/_scripts/"):
        return False
    return True


# Within tier 0, lower = earlier (HANDOVER and entry README before contract files).
TIER0_ORDER: dict[str, int] = {
    "HANDOVER.md": 0,
    "docs/README.md": 1,
    "docs/SYNC_CONTRACT.md": 2,
    "docs/sync-contract-execution-checklist.md": 3,
}


def classify_work_priority(rel: str) -> tuple[int, int | str]:
    """Sort key: (tier, tiebreaker). Lower tier = sooner; design/ last."""
    p = rel.replace("\\", "/")
    # Tier 0 — 入口、交接、同步契约（顺序见 TIER0_ORDER）
    if p in TIER0_ORDER:
        return (0, TIER0_ORDER[p])
    if p.startswith("docs/sync_design/"):
        return (0, 4)
    # Tier 1 — docs 根目录专章（总览、协议、Entangled 等）
    if p.startswith("docs/") and p.count("/") == 1:
        return (1, p.lower())
    # Tier 2 — runbooks / misc / 小目录索引（联调、运维）
    if p.startswith("docs/runbooks/") or p.startswith("docs/misc/") or p.startswith("docs/vnc/") or p.startswith("docs/review/"):
        return (2, p.lower())
    if p.startswith("docs/icons/"):
        return (2, p.lower())
    # Tier 3 — 审核点、子模块 README
    if p.startswith("docs/agent-approve-points/"):
        return (3, p.lower())
    if p.startswith("docs/submodules/"):
        return (4, p.lower())
    # Tier 5 — 专题目录（仍先于 design）
    if p.startswith("docs/gateway-upgrade/") or p.startswith("docs/ota/") or p.startswith("docs/p2p/"):
        return (5, p.lower())
    if p.startswith("docs/device/"):
        return (6, p.lower())
    if p.startswith("docs/research/"):
        return (7, p.lower())
    # Tier 8 — design 过程稿（数量大，放最后避免阻塞入口与契约）
    if p.startswith("docs/design/"):
        return (8, p.lower())
    return (3, p.lower())


def collect_paths() -> list[str]:
    out: list[Path] = []
    for p in sorted(DOCS.rglob("*.md")):
        if "node_modules" in str(p):
            continue
        out.append(p)
    handover = REPO / "HANDOVER.md"
    if handover.is_file():
        out.append(handover)
    rels = sorted({str(p.relative_to(REPO)).replace("\\", "/") for p in out})
    return rels


def main() -> None:
    state = load_state()
    paths = collect_paths()
    by_status: dict[str, list[str]] = defaultdict(list)
    for rel in paths:
        entry = state.get(rel, {})
        st = entry.get("status", "pending")
        by_status[st].append(rel)

    lines: list[str] = [
        "# 文档持疑核验登记（全量）",
        "",
        "> **方法**：每篇 **一个** subagent（或人工一轮），只对照 **该文件** 与代码；模板见 [`_scripts/SKEPTICAL_VERIFY_TEMPLATE.md`](_scripts/SKEPTICAL_VERIFY_TEMPLATE.md)。",
        "> **进度**：`docs/_scripts/verification_state.json`（仅记录非 pending）；重生成本表：`python3 docs/_scripts/regen_verification_registry.py`。",
        "",
        "## 统计",
        "",
    ]

    total = len(paths)
    pending = sum(1 for r in paths if state.get(r, {}).get("status", "pending") == "pending")
    verified = len(by_status.get("verified", []))
    partial = len(by_status.get("partial", []))
    skipped = len(by_status.get("skipped", [])) + len(by_status.get("generated", []))
    stale = len(by_status.get("stale", []))

    lines.append(f"- **仓库内 `.md` 计数（含 `docs/` + 根 `HANDOVER.md`）**：{total}")
    lines.append(f"- **pending（待核验）**：{pending}")
    lines.append(f"- **verified**：{verified} · **partial**：{partial} · **stale**：{stale} · **skipped/generated**：{skipped}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 全表（路径 → 层级 → 状态）")
    lines.append("")
    lines.append("| 路径 | 层级 | 状态 | 备注 |")
    lines.append("|------|------|------|------|")

    for rel in paths:
        tier = classify_tier(rel)
        entry = state.get(rel, {})
        st = entry.get("status", "pending")
        notes = entry.get("notes", "").replace("|", "\\|")
        if st == "pending":
            notes = notes or "—"
        lines.append(f"| `{rel}` | {tier} | {st} | {notes} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 批量分批（可选）")
    lines.append("")
    lines.append(
        "生成 **待办总表**（每批 "
        f"{BATCH_SIZE} 个）：见 [`PENDING_DOC_VERIFICATION.md`](PENDING_DOC_VERIFICATION.md)；"
        "CSV：`python3 docs/_scripts/emit_verify_batches.py`"
    )
    lines.append("")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH.relative_to(REPO)} ({total} paths)")

    # --- 待检查总表（仅 pending 工作队列，按 BATCH_SIZE 分批）---
    work: list[str] = [r for r in paths if is_work_pending(r, state)]
    work.sort(key=classify_work_priority)

    plines: list[str] = [
        "# 待检查文件总表（持疑核对 + 修文档）",
        "",
        "> **自动生成**：`python3 docs/_scripts/regen_verification_registry.py`",
        "> **规则**：每批 **"
        + str(BATCH_SIZE)
        + "** 个并行 subagent；每人 **只负责一个文件**，对照代码核验，**有矛盾则改文档**（过程稿可加页眉说明「历史」）。",
        "> **完成后**：把该路径写入 `docs/_scripts/verification_state.json`（`verified` 或 `partial` + 日期 + 备注），再重跑本脚本。",
        "> **并行 8 名**：每人只改自己的 `.md`；**登记**一律用 `python3 docs/_scripts/merge_verification_state.py ...`（**flock**，可多进程并行调用）。**禁止**多人手写覆盖整份 `verification_state.json`。",
        "> **partial**：仍出现在下表中，直至改为 `verified` / `skipped`（或删 JSON 项回到 pending）。",
        "> **模板**：[`_scripts/SKEPTICAL_VERIFY_TEMPLATE.md`](_scripts/SKEPTICAL_VERIFY_TEMPLATE.md)",
        "> **派单顺序**：按 **优先级** 排列（先 `HANDOVER` / `README` / `SYNC_CONTRACT` / checklist、`docs/` 根专章，再 `misc/`，**`design/` 最后**）。逻辑见 `regen_verification_registry.py` 中 `classify_work_priority`。",
        "",
        "## 统计",
        "",
        f"- **仍待派出核对/修复**：{len(work)}",
        f"- **批次数**（每批 {BATCH_SIZE}）：{(len(work) + BATCH_SIZE - 1) // BATCH_SIZE if work else 0}",
        "",
        "---",
        "",
    ]

    if not work:
        plines.append("（当前无待办；全部已 `verified` / 已标记 `generated` / `skipped`。）")
        plines.append("")
    else:
        plines.append("## 分批清单（按顺序派单）")
        plines.append("")
        batch_id = 0
        for i in range(0, len(work), BATCH_SIZE):
            batch_id += 1
            chunk = work[i : i + BATCH_SIZE]
            plines.append(f"### 第 {batch_id} 批（{len(chunk)} 个）")
            plines.append("")
            plines.append("| # | 路径 | 层级 |")
            plines.append("|---|------|------|")
            for j, rel in enumerate(chunk, start=1):
                tier = classify_tier(rel)
                plines.append(f"| {j} | `{rel}` | {tier} |")
            plines.append("")

        plines.append("---")
        plines.append("")
        plines.append("## 仅路径列表（复制用）")
        plines.append("")
        plines.append("```text")
        for rel in work:
            plines.append(rel)
        plines.append("```")
        plines.append("")

    PENDING_TABLE_PATH.write_text("\n".join(plines) + "\n", encoding="utf-8")
    print(f"Wrote {PENDING_TABLE_PATH.relative_to(REPO)} ({len(work)} pending)")


if __name__ == "__main__":
    main()
