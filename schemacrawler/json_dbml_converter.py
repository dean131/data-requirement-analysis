#!/usr/bin/env python3
# Convert all SchemaCrawler JSON exports in a folder into dbdiagram (DBML) code.
# Usage:
#   python json_dbml_converter.py /path/to/input_jsons /path/to/output_dbml

import sys, os, json, re
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_java_container(obj):
    return isinstance(obj, list) and len(obj) >= 2 and isinstance(obj[0], str) and obj[0].startswith('java.util')

def unwrap(obj):
    return obj[1] if is_java_container(obj) else obj

def collect_uuid_map(obj, uuid_map):
    if isinstance(obj, dict):
        uid = obj.get('@uuid')
        if uid:
            uuid_map[uid] = obj
        for v in obj.values():
            collect_uuid_map(v, uuid_map)
    elif isinstance(obj, list):
        for item in obj:
            collect_uuid_map(item, uuid_map)

def resolve_datatype(dtref, uuid_map):
    if isinstance(dtref, dict):
        return dtref.get('name') or dtref.get('database-specific-type-name') or dtref.get('full-name') or 'varchar'
    if isinstance(dtref, str):
        o = uuid_map.get(dtref)
        if o:
            return o.get('name') or o.get('database-specific-type-name') or o.get('full-name') or 'varchar'
    return 'varchar'

def sanitize_identifier(name):
    if name is None:
        return ''
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
        return name
    return f'`{name}`'

def format_default(val):
    if val is None or val == '':
        return None
    v = str(val).replace('\n', ' ')
    return f'`{v}`'

def get_table_obj(entry, uuid_map):
    return entry if isinstance(entry, dict) else uuid_map.get(entry)

def convert_to_dbml(json_path):
    """Convert a single SchemaCrawler JSON file to DBML string."""
    data = load_json(json_path)
    uuid_map = {}
    collect_uuid_map(data, uuid_map)

    catalog = data.get('catalog', {})
    table_entries = unwrap(catalog.get('tables', [])) or []
    tables = [get_table_obj(e, uuid_map) for e in table_entries if get_table_obj(e, uuid_map)]

    all_table_columns = unwrap(data.get('all-table-columns', [])) or []
    col_by_id = {c.get('@uuid'): c for c in all_table_columns if isinstance(c, dict)}

    out_lines, refs = [], []

    for t in tables:
        table_name = t.get('name') or t.get('full-name')
        table_note = (t.get('remarks') or '').strip()

        col_ids = unwrap(t.get('columns', [])) or []
        cols = [col_by_id[cid] for cid in col_ids if cid in col_by_id]
        cols.sort(key=lambda c: c.get('ordinal-position', 0))

        pk_cols = []
        pk_id = t.get('primary-key')
        if pk_id and pk_id in uuid_map:
            pk_obj = uuid_map[pk_id]
            pk_col_ids = unwrap(pk_obj.get('columns', [])) or []
            pk_cols = [col_by_id[cid]['name'] for cid in pk_col_ids if cid in col_by_id]

        out_lines.append(f"Table {sanitize_identifier(table_name)} {{")
        for c in cols:
            cname = c.get('name')
            ctype = resolve_datatype(c.get('column-data-type'), uuid_map) or 'varchar'
            attrs = []
            if cname in pk_cols and len(pk_cols) == 1:
                attrs.append('pk')
            if not c.get('nullable', True):
                attrs.append('not null')
            if c.get('part-of-unique-index', False) and (cname not in pk_cols):
                attrs.append('unique')
            dval = format_default(c.get('default-value'))
            if dval:
                attrs.append(f'default: {dval}')
            note = (c.get('remarks') or '').strip()
            if note:
                safe_note = note.replace("'", "''")
                attrs.append(f"note: '{safe_note}'")
            attr_str = ' [' + ', '.join(attrs) + ']' if attrs else ''
            out_lines.append(f"  {sanitize_identifier(cname)} {ctype}{attr_str}")

        if table_note:
            safe_tbl_note = table_note.replace("'", "''")
            out_lines.append(f"  Note: '{safe_tbl_note}'")

        # Indexes
        idxs = unwrap(t.get('table-constraints', [])) or []
        index_entries = [uuid_map[iid] for iid in idxs if iid in uuid_map and uuid_map[iid].get('@class', '').endswith('MutableIndex')]
        index_lines = []

        if pk_id and pk_id in uuid_map:
            pk_obj = uuid_map[pk_id]
            pk_cols_ids = unwrap(pk_obj.get('columns', [])) or []
            if len(pk_cols_ids) > 1:
                pk_names = [col_by_id[cid]['name'] for cid in pk_cols_ids if cid in col_by_id]
                cols_list = ', '.join(sanitize_identifier(n) for n in pk_names)
                index_lines.append(f"  ({cols_list}) [pk]")

        for idx in index_entries:
            if idx.get('@uuid') == pk_id:
                continue
            if not idx.get('unique', False):
                continue
            cols_ids = unwrap(idx.get('columns', [])) or []
            if not cols_ids:
                continue
            names = [col_by_id[cid]['name'] for cid in cols_ids if cid in col_by_id]
            cols_list = ', '.join(sanitize_identifier(n) for n in names)
            index_lines.append(f"  ({cols_list}) [unique]")

        if index_lines:
            out_lines.append("  indexes {")
            out_lines.extend(index_lines)
            out_lines.append("  }")

        out_lines.append("}\n")

        # Foreign keys
        fk_entries = unwrap(t.get('foreign-keys', [])) or []
        for fk_entry in fk_entries:
            fk = fk_entry if isinstance(fk_entry, dict) else uuid_map.get(fk_entry)
            if not fk or not isinstance(fk, dict):
                continue
            ref_table = uuid_map.get(fk.get('referenced-table'), {}) if isinstance(fk.get('referenced-table'), str) else fk.get('referenced-table', {})
            ref_table_name = ref_table.get('name') or ref_table.get('full-name')
            col_refs = unwrap(fk.get('column-references', [])) or []
            for cr in col_refs:
                fk_col = col_by_id.get(cr.get('foreign-key-column'), {}).get('name')
                pk_col = col_by_id.get(cr.get('primary-key-column'), {}).get('name')
                if not fk_col or not pk_col:
                    continue
                delete_rule = fk.get('delete-rule', ['',''])[1] if isinstance(fk.get('delete-rule'), list) else ''
                update_rule = fk.get('update-rule', ['',''])[1] if isinstance(fk.get('update-rule'), list) else ''
                opts = []
                if delete_rule:
                    opts.append(f"delete: {delete_rule}")
                if update_rule:
                    opts.append(f"update: {update_rule}")
                opt_str = f" [{', '.join(opts)}]" if opts else ""
                if ref_table_name == table_name and pk_col == fk_col:
                    continue
                refs.append(f"Ref: {sanitize_identifier(ref_table_name)}.{sanitize_identifier(pk_col)} > "
                            f"{sanitize_identifier(table_name)}.{sanitize_identifier(fk_col)}{opt_str}")

    return '\n'.join(out_lines + refs)

def main():
    if len(sys.argv) < 3:
        print("Usage: python json_dbml_converter.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])
    output_folder.mkdir(parents=True, exist_ok=True)

    json_files = list(input_folder.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_folder}")
        sys.exit(0)

    print(f"📂 Converting {len(json_files)} files from {input_folder} to {output_folder}")

    for json_file in json_files:
        try:
            dbml_content = convert_to_dbml(json_file)
            output_path = output_folder / (json_file.stem + ".dbml")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(dbml_content)
            print(f"✅ {json_file.name} → {output_path.name}")
        except Exception as e:
            print(f"❌ Failed to convert {json_file.name}: {e}")

    print("🎉 Conversion completed for all files!")

if __name__ == "__main__":
    main()
