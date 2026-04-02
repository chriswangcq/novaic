#!/usr/bin/env python3
"""
Verify novaic-app entity stores align with `generated_entity_id_fields.json`:

- createListStore / createStreamStore: `getId` must read the JSON id_field.
- createFormStore: `entityId: 'camelParam'` or first `keyParams` entry (camelCase)
  must snake_case-match the JSON id_field (same as toSnakeParams + entity_get id).

Skips form blocks with dynamic `entityId: () =>` and entities in SKIP_FORM_NO_PARAM.

Usage (repo root):  python3 scripts/check_entity_store_pk.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_ENTITIES_DIR = REPO_ROOT / "novaic-app" / "src" / "data" / "entities"
ID_FIELDS_JSON = (
    REPO_ROOT / "novaic-app" / "src" / "data" / "entangled" / "generated_entity_id_fields.json"
)

GET_ID_RE = re.compile(
    r"getId\s*:\s*\([^)]*\)\s*=>\s*(?:String\s*\(\s*)?(\w+)\s*\.\s*(\w+)\s*\)?",
    re.MULTILINE,
)
NAME_RE = re.compile(r"name\s*:\s*'([^']+)'")
FORM_ENTITY_ID_STR = re.compile(r"entityId\s*:\s*'([^']+)'")
FORM_ENTITY_ID_DYNAMIC = re.compile(r"entityId\s*:\s*\(")
KEY_PARAMS_BRACKET = re.compile(r"keyParams\s*:\s*\[(.*?)\]", re.DOTALL)

# Form id not expressed as entityId: 'x' / keyParams[0] in the store file.
SKIP_FORM_NO_PARAM = frozenset({"user-preferences", "users"})


def camel_to_snake(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name).replace("-", "_").lower()
    return s


def _brace_blocks_after(content: str, needle: str) -> list[str]:
    out: list[str] = []
    pos = 0
    while True:
        i = content.find(needle, pos)
        if i < 0:
            break
        j = content.find("{", i)
        if j < 0:
            break
        depth = 0
        k = j
        while k < len(content):
            c = content[k]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    out.append(content[j + 1 : k])
                    pos = k + 1
                    break
            k += 1
        else:
            print(f"[check_entity_store_pk] Unbalanced braces after {needle!r}", file=sys.stderr)
            sys.exit(1)
    return out


def _extract_list_stream(ts_path: Path) -> list[tuple[str, str]]:
    text = ts_path.read_text(encoding="utf-8")
    pairs: list[tuple[str, str]] = []
    for needle in ("createListStore<", "createStreamStore<"):
        if needle not in text:
            continue
        for block in _brace_blocks_after(text, needle):
            nm = NAME_RE.search(block)
            gid = GET_ID_RE.search(block)
            if not nm:
                print(f"[check_entity_store_pk] {ts_path.relative_to(REPO_ROOT)}: missing name: in list/stream block", file=sys.stderr)
                sys.exit(1)
            if not gid:
                print(
                    f"[check_entity_store_pk] {ts_path.relative_to(REPO_ROOT)}: missing getId: for entity {nm.group(1)!r}",
                    file=sys.stderr,
                )
                sys.exit(1)
            pairs.append((nm.group(1), gid.group(2)))
    return pairs


def _form_camel_param(block: str) -> str | None:
    if FORM_ENTITY_ID_DYNAMIC.search(block):
        return None
    m = FORM_ENTITY_ID_STR.search(block)
    if m:
        return m.group(1)
    km = KEY_PARAMS_BRACKET.search(block)
    if not km:
        return None
    parts = re.findall(r"'([^']+)'", km.group(1))
    if len(parts) >= 1:
        return parts[0]
    return None


def _validate_form(ts_path: Path, entity: str, block: str, entities_json: dict[str, str], errors: list[str]) -> None:
    expected = entities_json.get(entity)
    if expected is None:
        errors.append(f"{ts_path.name}: form entity {entity!r} not in generated_entity_id_fields.json")
        return

    camel = _form_camel_param(block)
    if camel is None:
        if entity in SKIP_FORM_NO_PARAM:
            return
        errors.append(
            f"{ts_path.name}: form {entity!r} has no string entityId / keyParams[0]; "
            f"if intentional add to SKIP_FORM_NO_PARAM or use entityId: 'param'"
        )
        return

    got_snake = camel_to_snake(camel)
    if got_snake != expected:
        errors.append(
            f"{ts_path.name}: form {entity!r} resolves id from {camel!r} → {got_snake!r} "
            f"but JSON id_field is {expected!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check entity store PK vs generated_entity_id_fields.json")
    parser.add_argument("--check", action="store_true", help="no-op flag")
    _ = parser.parse_args()

    if not ID_FIELDS_JSON.is_file():
        print(f"[check_entity_store_pk] Missing {ID_FIELDS_JSON}", file=sys.stderr)
        sys.exit(1)

    doc = json.loads(ID_FIELDS_JSON.read_text(encoding="utf-8"))
    entities: dict[str, str] = doc.get("entities") or {}

    errors: list[str] = []

    for ts_path in sorted(APP_ENTITIES_DIR.glob("*.ts")):
        if ts_path.name == "__generated__.ts":
            continue
        text = ts_path.read_text(encoding="utf-8")

        for entity, field in _extract_list_stream(ts_path):
            expected = entities.get(entity)
            if expected is None:
                errors.append(f"{ts_path.name}: entity {entity!r} not in generated_entity_id_fields.json")
                continue
            if field != expected:
                errors.append(
                    f"{ts_path.name}: entity {entity!r} getId uses .{field!r} but JSON id_field is {expected!r}"
                )

        if "createFormStore<" in text:
            for block in _brace_blocks_after(text, "createFormStore<"):
                nm = NAME_RE.search(block)
                if nm:
                    _validate_form(ts_path, nm.group(1), block, entities, errors)

    if errors:
        print("[check_entity_store_pk] FAIL:\n  " + "\n  ".join(errors), file=sys.stderr)
        sys.exit(1)

    print("[check_entity_store_pk] OK: list/stream getId + form id param match generated_entity_id_fields.json")


if __name__ == "__main__":
    main()
