#!/usr/bin/env python3
"""
scripts/generate_entity_types.py — Entangled Schema Codegen

从 Python EntityDef（single source of truth）自动生成：
  1. TypeScript interfaces  → novaic-app/src/data/entities/__generated__.ts
  2. Rust type hints file   → novaic-app/src-tauri/src/types/entities_generated.rs (仅文档用，不编译)

用法:
  python scripts/generate_entity_types.py [--check]

  --check  校验模式：不写文件，只检查生成内容是否与磁盘一致（供 CI 使用）

设计原则:
  - 所有 TypeScript 类型从 FieldDef.kind 自动推断
  - hidden=True 的字段不出现在 TS 接口中（和 API 行为一致）
  - 生成文件头部注明"DO NOT EDIT"并包含 checksum，detect drift
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import textwrap
from pathlib import Path
from typing import List

# ── Path setup ──────────────────────────────────────────────────────────────
# Allow running from repo root or scripts/ directory
SCRIPT_DIR   = Path(__file__).parent
REPO_ROOT    = SCRIPT_DIR.parent
GATEWAY_DIR  = REPO_ROOT / "novaic-gateway"
BUSINESS_DIR = REPO_ROOT / "novaic-business"
DEVICE_DIR   = REPO_ROOT / "novaic-device"
COMMON_DIR   = REPO_ROOT / "novaic-common"
ENTANGLED_PY = REPO_ROOT / "Entangled" / "packages" / "server-python"
APP_DIR      = REPO_ROOT / "novaic-app"

sys.path.insert(0, str(ENTANGLED_PY))
sys.path.insert(0, str(GATEWAY_DIR))
sys.path.insert(0, str(BUSINESS_DIR))
sys.path.insert(0, str(DEVICE_DIR))
sys.path.insert(0, str(COMMON_DIR))

# ── Import entity defs ───────────────────────────────────────────────────────
# Minimal stub to avoid pulling in all of Gateway's dependencies
import importlib.util

def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# ── FieldKind → TypeScript type mapping ─────────────────────────────────────
from gateway.entity.store import FieldKind, FieldDef, EntityDef

FIELD_KIND_TO_TS: dict[FieldKind, str] = {
    FieldKind.TEXT:      "string",
    FieldKind.INTEGER:   "number",
    FieldKind.REAL:      "number",
    FieldKind.BLOB:      "string",      # base64 string in practice
    FieldKind.JSON:      "unknown",     # caller should assert specific type
    FieldKind.BOOL:      "boolean",
    FieldKind.TIMESTAMP: "string",      # ISO 8601 string
}

# Well-known JSON fields with specific TS types (override FIELD_KIND_TO_TS for JSON)
JSON_FIELD_OVERRIDES: dict[tuple[str, str], str] = {
    # (entity_name, field_name) → ts_type
    ("agents",       "vm_config"):              "Record<string, unknown>",
    ("agents",       "ports"):                  "Record<string, unknown>",
    ("agents",       "android_config"):         "Record<string, unknown> | null",
    ("devices",      "ports"):                  "Record<string, unknown>",
    ("messages",     "content"):                "{ text: string; attachments: unknown[] }",
    ("messages",     "metadata"):               "Record<string, unknown>",
    ("skills",       "tools"):                  "string[]",
    ("skills",       "auto_match_keywords"):    "string[]",
    ("agent-tools",  "personality"):            "Record<string, unknown>",
    ("agent-tools",  "user_profile"):           "Record<string, unknown>",
    ("agent-tools",  "enabled_tool_categories"):"string[]",
    ("agent-tools",  "disabled_tools"):         "string[]",
    ("agent-tools",  "growth_log"):             "unknown[]",
    ("agent-tools",  "drive_config"):           "Record<string, unknown>",
    ("agent-binding","mounted_tools"):          "string[]",
    ("agent-state",  "wake_triggers"):          "unknown[]",
    ("subagents",    "wake_triggers"):          "unknown[]",
    ("subagents",    "tool_ports"):             "Record<string, unknown> | null",
    ("execution-logs","data"):                  "Record<string, unknown>",
    ("log-payloads", "input"):                  "Record<string, unknown>",
    ("log-payloads", "result"):                 "Record<string, unknown>",
    ("agent-notebook","related_topics"):        "string[]",
    ("agent-memory", "value"):                  "unknown",
    ("agent-tasks",  "related_profile_keys"):   "string[]",
    ("agent-tasks",  "progress_notes"):         "unknown[]",
}


def field_to_ts_type(entity_name: str, f: FieldDef) -> str:
    """Convert a FieldDef to its TypeScript type string."""
    if f.kind == FieldKind.JSON:
        override = JSON_FIELD_OVERRIDES.get((entity_name, f.name))
        if override:
            return override
        return "unknown"
    return FIELD_KIND_TO_TS[f.kind]


def entity_to_ts_interface(defn: EntityDef) -> str:
    """Generate a TypeScript interface for one EntityDef."""
    # Interface name: PascalCase from entity name (e.g. "agent-tools" → AgentTools)
    iface_name = "".join(
        word.capitalize()
        for word in defn.name.replace("-", "_").split("_")
    ) + "Entity"

    lines = [f"export interface {iface_name} {{"]
    for f in defn.fields:
        if f.hidden:
            continue  # hidden fields never appear in API responses
        ts_type = field_to_ts_type(defn.name, f)
        optional = "?" if f.nullable and not f.primary else ""
        lines.append(f"  {f.name}{optional}: {ts_type};")
    lines.append("}")
    return "\n".join(lines)


def generate_ts(all_defs: List[EntityDef]) -> str:
    """Generate the full TypeScript output."""
    blocks = []
    for defn in all_defs:
        if not defn.fields:
            continue  # skip entities without field definitions
        blocks.append(entity_to_ts_interface(defn))

    entity_union = " | ".join(
        "".join(w.capitalize() for w in d.name.replace("-", "_").split("_")) + "Entity"
        for d in all_defs if d.fields
    )

    content = textwrap.dedent(f"""\
        /**
         * THIS FILE IS AUTO-GENERATED. DO NOT EDIT MANUALLY.
         *
         * Generated from: novaic-business/business/schema_push.py
         *                 + novaic-device/device/schema_push.py
         * Generator:      scripts/generate_entity_types.py
         *
         * Regenerate:  python scripts/generate_entity_types.py
         * CI check:    python scripts/generate_entity_types.py --check
         */

        // ── Entity Interfaces ────────────────────────────────────────────────────────

        {chr(10).join(blocks)}

        // ── Union type of all entities ────────────────────────────────────────────────
        export type AnyEntity = {entity_union};

        // ── Entity name → interface map (for generic code) ───────────────────────────
        export type EntityName = AnyEntity extends infer E
          ? E extends {{ id: string }}
            ? string
            : never
          : never;
    """)
    return content


def checksum(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TypeScript types from EntityDef")
    parser.add_argument("--check", action="store_true", help="Check mode (no file writes, exit 1 on drift)")
    args = parser.parse_args()

    # Load entity defs from the current schema owners.
    from business.schema_push import ALL_BUSINESS_ENTITIES
    from device.schema_push import ALL_DEVICE_ENTITIES
    all_entities = list(ALL_BUSINESS_ENTITIES.values()) + list(ALL_DEVICE_ENTITIES.values())

    ts_content = generate_ts(all_entities)
    cs = checksum(ts_content)

    # Inject checksum into header
    ts_final = ts_content.replace(
        "// ── Entity Interfaces",
        f"// checksum: {cs}\n\n// ── Entity Interfaces",
    )

    out_path = APP_DIR / "src" / "data" / "entities" / "__generated__.ts"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.check:
        if not out_path.exists():
            print(f"[codegen] FAIL: {out_path} does not exist. Run: python scripts/generate_entity_types.py")
            sys.exit(1)
        existing = out_path.read_text()
        existing_cs = checksum(existing)
        new_cs = checksum(ts_final)
        if existing_cs != new_cs:
            print(
                f"[codegen] DRIFT DETECTED: {out_path.relative_to(REPO_ROOT)}\n"
                f"  Expected checksum: {new_cs}\n"
                f"  Actual checksum:   {existing_cs}\n"
                f"  Run: python scripts/generate_entity_types.py"
            )
            sys.exit(1)
        print(f"[codegen] OK: {out_path.relative_to(REPO_ROOT)} is up to date.")
    else:
        out_path.write_text(ts_final)
        entity_count = sum(1 for d in all_entities if d.fields)
        print(f"[codegen] Generated {entity_count} entity interfaces → {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
