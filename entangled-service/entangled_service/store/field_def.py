"""FieldKind / FieldDef / F factory — migrated from Gateway store.py, zero business logic."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class FieldKind(str, Enum):
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BLOB = "BLOB"
    JSON = "JSON"
    BOOL = "BOOL"
    TIMESTAMP = "TIMESTAMP"


@dataclass
class FieldDef:
    name: str
    kind: FieldKind
    primary: bool = False
    nullable: bool = True
    default: Any = None
    unique: bool = False
    index: bool = False
    ref: Optional[str] = None
    hidden: bool = False

    @property
    def sql_type(self) -> str:
        _map = {
            FieldKind.TEXT: "TEXT",
            FieldKind.INTEGER: "INTEGER",
            FieldKind.REAL: "REAL",
            FieldKind.BLOB: "BLOB",
            FieldKind.JSON: "TEXT",
            FieldKind.BOOL: "INTEGER",
            FieldKind.TIMESTAMP: "TEXT",
        }
        return _map[self.kind]

    def column_ddl(self) -> str:
        return self._build_ddl(include_pk=True)

    def column_ddl_no_pk(self) -> str:
        """DDL without PRIMARY KEY (for composite PK via table constraint)."""
        return self._build_ddl(include_pk=False)

    def _build_ddl(self, include_pk: bool = True) -> str:
        parts = [self.name, self.sql_type]
        if self.primary and include_pk:
            parts.append("PRIMARY KEY")
        if not self.nullable and not self.primary:
            parts.append("NOT NULL")
        if self.unique and not self.primary:
            parts.append("UNIQUE")
        if self.default is not None:
            if self.default == "NOW":
                parts.append("DEFAULT (datetime('now'))")
            elif isinstance(self.default, str):
                parts.append(f"DEFAULT '{self.default}'")
            elif isinstance(self.default, bool):
                parts.append(f"DEFAULT {1 if self.default else 0}")
            else:
                parts.append(f"DEFAULT {self.default}")
        if self.ref:
            parts.append(f"REFERENCES {self.ref}")
        return " ".join(parts)

    @property
    def is_json(self) -> bool:
        return self.kind == FieldKind.JSON

    @property
    def is_bool(self) -> bool:
        return self.kind == FieldKind.BOOL

    @property
    def is_timestamp(self) -> bool:
        return self.kind == FieldKind.TIMESTAMP

    def serialize(self, value: Any) -> Any:
        if value is None:
            return None
        if self.is_json:
            return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        if self.is_bool:
            return 1 if value else 0
        return value

    def deserialize(self, value: Any) -> Any:
        if value is None:
            return None
        if self.is_json:
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value
        if self.is_bool:
            return bool(value)
        return value

    def to_spec(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "primary": self.primary,
            "nullable": self.nullable,
            "default": self.default,
            "unique": self.unique,
            "index": self.index,
            "ref": self.ref,
            "hidden": self.hidden,
        }

    @classmethod
    def from_spec(cls, spec: dict) -> FieldDef:
        return cls(
            name=spec["name"],
            kind=FieldKind(spec["kind"]),
            primary=spec.get("primary", False),
            nullable=spec.get("nullable", True),
            default=spec.get("default"),
            unique=spec.get("unique", False),
            index=spec.get("index", False),
            ref=spec.get("ref"),
            hidden=spec.get("hidden", False),
        )


class F:
    """FieldDef factory — mirrors Gateway's F class."""

    @staticmethod
    def text(name: str, *, primary: bool = False, nullable: bool = True,
             default: Any = None, unique: bool = False, index: bool = False,
             ref: Optional[str] = None, hidden: bool = False) -> FieldDef:
        return FieldDef(name, FieldKind.TEXT, primary=primary, nullable=nullable,
                        default=default, unique=unique, index=index, ref=ref, hidden=hidden)

    @staticmethod
    def int_(name: str, *, primary: bool = False, nullable: bool = True, default: Any = None,
             unique: bool = False, index: bool = False, ref: Optional[str] = None,
             hidden: bool = False) -> FieldDef:
        return FieldDef(name, FieldKind.INTEGER, primary=primary, nullable=nullable,
                        default=default, unique=unique, index=index, ref=ref, hidden=hidden)

    @staticmethod
    def real(name: str, *, nullable: bool = True, default: Any = None) -> FieldDef:
        return FieldDef(name, FieldKind.REAL, nullable=nullable, default=default)

    @staticmethod
    def json(name: str, *, nullable: bool = True, default: Any = None) -> FieldDef:
        return FieldDef(name, FieldKind.JSON, nullable=nullable, default=default)

    @staticmethod
    def bool_(name: str, *, default: bool = False) -> FieldDef:
        return FieldDef(name, FieldKind.BOOL, nullable=False, default=default)

    @staticmethod
    def timestamp(name: str, *, auto: bool = True, nullable: bool = True) -> FieldDef:
        return FieldDef(name, FieldKind.TIMESTAMP, nullable=nullable,
                        default="NOW" if auto else None)

    @staticmethod
    def blob(name: str, *, nullable: bool = True) -> FieldDef:
        return FieldDef(name, FieldKind.BLOB, nullable=nullable)
