#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert a SchemaCrawler-exported JSON to dbdiagram.io DBML
✅ Updated to sanitize SQL default expressions such as nextval('...') to DBML-safe string literals.
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def index_by_uuid(obj):
    """Walk entire JSON tree and build an index of objects by @uuid."""
    index = {}
    def walk(o):
        if isinstance(o, dict):
            uid = o.get("@uuid")
            if isinstance(uid, str):
                index[uid] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    return index


def safe_ident(name: str) -> str:
    """Quote identifiers that contain spaces or special characters."""
    if name is None:
        return '""'
    bad = ' -.:/\\`"\''
    if any(c in name for c in bad):
        return f'"{name}"'
    return name


def resolve_db_type(col_obj, uuid_index):
    """Resolve column data type and width/size from SchemaCrawler object."""
    type_uuid = col_obj.get("type")
    base = "text"
    if type_uuid and type_uuid in uuid_index:
        t = uuid_index[type_uuid]
        base = (
            t.get("database-specific-type-name")
            or t.get("local-type-name")
            or t.get("standard-type-name")
            or base
        )

    width = col_obj.get("width")
    size = col_obj.get("size")
    size_str = ""
    if isinstance(width, str) and width.strip().startswith("("):
        size_str = width.strip()
    elif isinstance(size, int) and size > 0:
        size_str = f"({size})"

    return f"{base}{size_str}"


def sanitize_default(default_value):
    """
    Sanitize default expressions for DBML compatibility.
    - Wrap SQL expressions like nextval('...') or now() in quotes.
    - Escape internal quotes.
    """
    if not default_value:
        return None

    dv = str(default_value).strip()

    # Detect SQL expressions that break DBML
    if re.search(r"[()]", dv) or "::" in dv or dv.lower().startswith(("nextval", "uuid_", "now", "current_", "gen_random_uuid")):
        dv = dv.replace('"', '\\"')
        return f'"{dv}"'

    # Basic safe default
    if any(c in dv for c in [' ', ':', "'", '"']):
        dv = dv.replace('"', '\\"')
        return f'"{dv}"'

    return dv


def to_dbml(input_json) -> str:
    uuid_index = index_by_uuid(input_json)
    cols_block = input_json.get("all-table-columns", [])
    columns = cols_block[1] if isinstance(cols_block, list) and len(cols_block) >= 2 else []

    tables = defaultdict(list)
    for col in columns:
        if not isinstance(col, dict):
            continue
        full = col.get("full-name")
        if not full or full.count(".") < 2:
            continue
        schema, table, colname = full.split(".", 2)

        col_entry = {
            "name": col.get("name") or colname,
            "type": resolve_db_type(col, uuid_index),
            "nullable": col.get("nullable", True),
            "default": sanitize_default(col.get("default-value")),
            "pk": col.get("part-of-primary-key", False),
            "unique": col.get("part-of-unique-index", False),
            "auto": col.get("auto-incremented", False),
            "generated": col.get("generated", False),
            "remarks": col.get("remarks") or "",
        }
        tables[(schema, table)].append(col_entry)

    lines = []
    for (schema, table), cols in sorted(tables.items()):
        tname = f"{schema}.{table}"
        lines.append(f"Table {safe_ident(tname)} {{")
        for c in cols:
            attrs = []
            if c["pk"]:
                attrs.append("pk")
            if c["unique"]:
                attrs.append("unique")
            if c["auto"]:
                attrs.append("increment")
            if not c["nullable"]:
                attrs.append("not null")
            if c["default"] not in (None, "", "null"):
                attrs.append(f"default: {c['default']}")
            attr_str = f" [{', '.join(attrs)}]" if attrs else ""
            note = ""
            if c["remarks"]:
                note = f" // {c['remarks'].replace('\"', '\\\"')}"
            lines.append(f"  {safe_ident(c['name'])} {c['type']}{attr_str}{note}")
        lines.append("}\n")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_schemacrawler_to_dbml.py input.json output.dbml")
        sys.exit(1)
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    data = load_json(in_path)
    dbml = to_dbml(data)
    out_path.write_text(dbml, encoding="utf-8")
    print(f"✅ Wrote DBML to {out_path}")


if __name__ == "__main__":
    main()
