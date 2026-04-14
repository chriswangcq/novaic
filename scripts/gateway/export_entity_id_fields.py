#!/usr/bin/env python3
"""
Generate gateway/entity/generated_entity_id_fields.json from ALL_ENTITIES (phase 3 / C.3 seed).

  python scripts/export_entity_id_fields.py          # write JSON
  python scripts/export_entity_id_fields.py --check  # exit 1 if file stale

Run from novaic-gateway repo root (or set NOVAIC_GATEWAY_ROOT).

After changing defs, copy the JSON to Rust + App (monorepo root):

  bash ../scripts/sync_entity_id_fields.sh
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
# defs.py pulls entangled + gateway.entity.store — need both roots on PYTHONPATH.
for p in (
    REPO_ROOT / "Entangled" / "packages" / "server-python",
    ROOT,
):
    ps = str(p)
    if ps not in sys.path:
        sys.path.insert(0, ps)


def build_payload() -> dict:
    from gateway.entity.defs import ALL_ENTITIES

    entities = {
        d.name: getattr(d, "id_field", "id") for d in ALL_ENTITIES
    }
    return {"version": 1, "entities": dict(sorted(entities.items()))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "gateway" / "entity" / "generated_entity_id_fields.json",
    )
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = build_payload()
    if args.check:
        if not args.out.is_file():
            print(f"missing {args.out}", file=sys.stderr)
            sys.exit(1)
        existing = json.loads(args.out.read_text(encoding="utf-8"))
        if existing != data:
            print(
                "generated_entity_id_fields.json is stale — run "
                "`python scripts/export_entity_id_fields.py` from novaic-gateway",
                file=sys.stderr,
            )
            sys.exit(1)
        print("ok")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(args.out)


if __name__ == "__main__":
    main()
