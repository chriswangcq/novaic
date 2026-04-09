"""EntityDef — merged Entangled BaseEntityDef + Gateway's typed field extensions.

No business hooks (actions, serializer, deserializer). Those stay in Gateway.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from entangled.server.defs import EntityDef as BaseEntityDef
from .field_def import FieldDef


@dataclass(kw_only=True)
class EntityDef(BaseEntityDef):
    table: str = ""
    id_field: str = "id"
    user_scoped: bool = True
    fields: List[FieldDef] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    default_order: str = "created_at"
    lock_type: str = "global"
    auto_timestamps: bool = True
    # (parent_entity_name, local_fk_column, parent_pk_column)
    parent: Optional[Tuple[str, str, str]] = None
    default_not_in_filters: Dict[str, List[Any]] = field(default_factory=dict)

    # ── DDL ────────────────────────────────────────────────────────────────

    def create_table_sql(self) -> str:
        if not self.fields:
            raise ValueError(f"EntityDef '{self.name}' has no fields, cannot generate DDL")
        pk_fields = [f for f in self.fields if f.primary]
        composite_pk = len(pk_fields) > 1
        if composite_pk:
            col_defs = [f.column_ddl_no_pk() for f in self.fields]
            pk_clause = f"PRIMARY KEY({', '.join(f.name for f in pk_fields)})"
            all_parts = col_defs + [pk_clause] + self.constraints
        else:
            col_defs = [f.column_ddl() for f in self.fields]
            all_parts = col_defs + self.constraints
        cols = ",\n    ".join(all_parts)
        return f"CREATE TABLE IF NOT EXISTS {self.table} (\n    {cols}\n);"

    def index_sqls(self) -> List[str]:
        stmts = []
        for f in self.fields:
            if f.index and not f.primary:
                stmts.append(
                    f"CREATE INDEX IF NOT EXISTS idx_{self.table}_{f.name} "
                    f"ON {self.table}({f.name});"
                )
        return stmts

    def alter_add_column_sqls(self, existing_cols: List[str]) -> List[str]:
        stmts = []
        for f in self.fields:
            if f.name not in existing_cols:
                stmts.append(f"ALTER TABLE {self.table} ADD COLUMN {f.column_ddl()};")
        return stmts

    # ── Field lookup ──────────────────────────────────────────────────────

    @property
    def field_map(self) -> Dict[str, FieldDef]:
        return {f.name: f for f in self.fields}

    @property
    def json_fields(self) -> List[str]:
        return [f.name for f in self.fields if f.is_json]

    @property
    def bool_fields(self) -> List[str]:
        return [f.name for f in self.fields if f.is_bool]

    @property
    def hidden_fields(self) -> List[str]:
        return [f.name for f in self.fields if f.hidden]

    @property
    def tracks_updated_at_column(self) -> bool:
        if not self.auto_timestamps or not self.fields:
            return False
        return any(f.name == "updated_at" for f in self.fields)

    # ── Spec serialization (for schema registration API) ──────────────────

    @classmethod
    def from_spec(cls, spec: dict) -> EntityDef:
        from .field_def import FieldDef as FD
        fields = [FD.from_spec(f) for f in spec.get("fields", [])]
        return cls(
            name=spec["name"],
            table=spec.get("table", spec["name"].replace("-", "_")),
            id_field=spec.get("id_field", "id"),
            user_scoped=spec.get("user_scoped", True),
            key_params=spec.get("key_params", []),
            fields=fields,
            constraints=spec.get("constraints", []),
            default_order=spec.get("default_order", "created_at"),
            lock_type=spec.get("lock_type", "global"),
            auto_timestamps=spec.get("auto_timestamps", True),
            sync_type=spec.get("sync_type", "list"),
            sync_limit=spec.get("sync_limit", 50),
            op_log_size=spec.get("op_log_size", 200),
            subscription_mode=spec.get("subscription_mode", "lazy"),
            data_order=spec.get("data_order", "desc"),
            default_not_in_filters=spec.get("default_not_in_filters", {}),
            parent=tuple(spec["parent"]) if spec.get("parent") else None,
        )
