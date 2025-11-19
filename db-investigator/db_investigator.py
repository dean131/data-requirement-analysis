import pandas as pd
import inspect
from sqlalchemy import create_engine, inspect as sqlalchemy_inspect, text
from sqlalchemy.exc import SQLAlchemyError
from collections import defaultdict

class DBTool:
    def __init__(self, username, password, host, port, dbname):
        """
        Initializes the database connection and the schema inspector.
        
        The inspector is initialized once during instantiation to avoid 
        overhead when performing multiple operations later.
        """
        # Construct the PostgreSQL connection string
        self.conn_str = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"
        
        try:
            self.engine = create_engine(self.conn_str)
            self.inspector = sqlalchemy_inspect(self.engine)
            print(f"[INFO] Successfully connected to database: {dbname}")
        except SQLAlchemyError as e:
            print(f"[ERROR] Connection failed: {e}")
            exit()

    def show_features(self):
        """
        Displays this list of available features.
        
        This method dynamically inspects the class to find all public methods,
        their parameters (signature), and their docstring (description).
        
        Usage: db_tool.show_features()
        """
        print("\n[INFO] Available Program Features:")
        print("-" * 30)
        
        # Iterate over all members of this class
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            
            if not name.startswith('_'):
                
                # 1. Get the method signature
                try:
                    signature = inspect.signature(method)
                except ValueError:
                    signature = "()" 

                # 2. Get the docstring
                doc = inspect.getdoc(method)
                if doc:
                    # Use only the first line of the docstring for a brief summary
                    description = doc.strip().split('\n')[0]
                else:
                    description = "No description available."
                
                # 3. Print the formatted feature
                print(f"  - {name}{signature}")
                print(f"    {description}\n")

    def list_tables(self, schema='public', list_all_schemas=False):
        """
        Retrieves and displays a list of tables.
        
        :param schema: The specific schema to query (default 'public').
        :param list_all_schemas: If True, ignores the 'schema' parameter and 
                                 lists tables from EVERY available schema in the database.
        
        Usage (Default Schema): db_tool.list_tables()
        Usage (All Schemas):    db_tool.list_tables(list_all_schemas=True)
        """
        all_tables_data = []
        
        # Determine which schemas to scan
        if list_all_schemas:
            print(f"\n[INFO] Scanning ALL schemas for tables...")
            try:
                # SQLAlchemy inspector can auto-discover all schema names
                target_schemas = self.inspector.get_schema_names()
            except Exception as e:
                print(f"[ERROR] Could not retrieve schema list: {e}")
                return
        else:
            print(f"\n[INFO] Fetching table list for schema: '{schema}'...")
            target_schemas = [schema]

        # Iterate through schemas and collect table names
        for s in target_schemas:
            try:
                tables = self.inspector.get_table_names(schema=s)
                for t in tables:
                    all_tables_data.append({"Schema": s, "Table Name": t})
            except Exception as e:
                # Some system schemas might be protected/hidden
                print(f"[WARN] Could not access schema '{s}': {e}")

        if not all_tables_data:
            print("[RESULT] No tables found.")
            return

        # Display results sorted by Schema then Table Name for readability
        df = pd.DataFrame(all_tables_data)
        df = df.sort_values(by=['Schema', 'Table Name'])
        print(df.to_markdown(index=False))

    def get_table_details(self, table_name, schema='public'):
        """
        Retrieves detailed metadata for a specific table, including column types,
        primary key constraints, and foreign key relationships.
        
        This aggregates data from three different introspection methods (get_columns, 
        get_pk_constraint, get_foreign_keys) into a single readable view.
        
        :param table_name: The name of the table to inspect.
        :param schema: The schema where the table resides.
        
        Usage: db_tool.get_table_details("users", schema="public")
        """
        print(f"\n[INFO] Inspecting metadata for table: '{table_name}'...")

        if not self.inspector.has_table(table_name, schema=schema):
            print(f"[ERROR] Table '{table_name}' does not exist.")
            return

        # 1. Retrieve basic column definitions
        columns = self.inspector.get_columns(table_name, schema=schema)
        
        # 2. Retrieve constraint data
        pk_info = self.inspector.get_pk_constraint(table_name, schema=schema)
        pks = pk_info.get('constrained_columns', [])

        fks = self.inspector.get_foreign_keys(table_name, schema=schema)
        fk_map = {}
        for fk in fks:
            for local_col, remote_col in zip(fk['constrained_columns'], fk['referred_columns']):
                fk_map[local_col] = f"{fk['referred_table']}.{remote_col}"

        # 3. Build a structured summary
        structured_data = []
        for col in columns:
            col_name = col['name']
            is_pk = "YES" if col_name in pks else ""
            fk_target = fk_map.get(col_name, "")
            
            structured_data.append({
                "Column": col_name,
                "Type": str(col['type']),
                "Nullable": col['nullable'],
                "Primary Key": is_pk,
                "Foreign Key": fk_target
            })

        # 4. Display formatted output
        df = pd.DataFrame(structured_data)
        print(df.to_markdown(index=False))

    def trace_value_across_db(self, search_data: dict, mode='OR', schema='public', 
                              scan_all_schemas=False, show_records=False, record_limit=5):
        """
        Traces one or more {column: value} pairs and sorts tables by match count.
        
        Can optionally display the actual matching records from the database.
        
        :param search_data: A dictionary (map) of {column: value} pairs to find.
                            Example: {'user_id': 123, 'email': 'test@example.com'}
        :param mode: 'OR' (default) - Finds tables matching ANY pair, sorts by match count.
                     'AND' - Finds tables where a SINGLE ROW matches ALL pairs.
        :param schema: The schema to scan (ignored if 'scan_all_schemas' is True).
        :param scan_all_schemas: Flag to enable scanning all schemas.
        :param show_records: (Optional) If True, displays the first 'record_limit' matching rows.
        :param record_limit: (Optional) Sets the number of records to display (default: 5).
        
        Usage (AND mode, Show Records): 
            data_map = {'wh_id': 254, 'pro_id': 780}
            db_tool.trace_value_across_db(data_map, mode='AND', scan_all_schemas=True, show_records=True)
        Usage (OR mode, sorted):
            db_tool.trace_value_across_db({'user_id': 123, 'vat': 11, 'pro_code': 'ABC'})
        """
        # --- 1. Input Validation ---
        mode = mode.upper()
        if mode not in ('AND', 'OR'):
            print(f"\n[ERROR] Invalid mode '{mode}'. Must be 'AND' or 'OR'.")
            return []
        
        if not isinstance(search_data, dict):
            print(f"\n[ERROR] Invalid input. 'search_data' must be a dictionary (map).")
            return []
        
        op = " AND " if mode == 'AND' else " OR "
        search_summary = op.join([f"({c} = {v})" for c, v in search_data.items()])
        
        print(f"\n[INFO] Tracing for pairs with mode: {mode}")
        if mode == 'AND':
            print(f"  Looking for: {search_summary}")

        found_matches = [] 
        
        # --- 2. Determine Schemas ---
        if scan_all_schemas:
            print("[INFO] Scanning ALL schemas.")
            try:
                target_schemas = self.inspector.get_schema_names()
            except Exception as e:
                print(f"[ERROR] Could not retrieve schema list: {e}")
                return []
        else:
            print(f"[INFO] Scanning single schema: '{schema}'.")
            target_schemas = [schema]

        # --- 3. Outer Schema Loop ---
        for s in target_schemas:
            print(f"\n--- Scanning Schema: {s} ---")
            try:
                all_tables = self.inspector.get_table_names(schema=s)
            except Exception as e:
                print(f"  [WARN] Could not access or list tables in schema '{s}', skipping: {e}")
                continue
            if not all_tables:
                print("  [INFO] No tables found in this schema.")
                continue

            # --- 4. Inner Table Loop ---
            for table in all_tables:
                print(f"  [Scan] Checking table: {table}...")
                try:
                    table_columns = [c['name'] for c in self.inspector.get_columns(table, schema=s)]
                except Exception as e:
                    print(f"    [WARN] Failed to inspect columns ({e}), skipping table.")
                    continue 
                
                # --- 5. LOGIC FOR 'AND' MODE ---
                if mode == 'AND':
                    required_cols = list(search_data.keys())
                    if all(col in table_columns for col in required_cols):
                        conditions = []
                        params = {}
                        for i, (col, val) in enumerate(search_data.items()):
                            param_name = f"val{i}"
                            conditions.append(f"{col}::text = :{param_name}")
                            params[param_name] = str(val)
                        
                        sql_conditions = " AND ".join(conditions)
                        select_clause = "*" if show_records else "1"
                        limit = record_limit if show_records else 1
                        sql = f"SELECT {select_clause} FROM {s}.{table} WHERE {sql_conditions} LIMIT {limit}"

                        print(f"    [Trace] Checking for '{search_summary}'...", end=" ")
                        try:
                            with self.engine.connect() as conn:
                                if show_records:
                                    df_results = pd.read_sql(text(sql), conn, params=params)
                                    result = not df_results.empty
                                else:
                                    result = conn.execute(text(sql), params).fetchone()
                            
                            if result:
                                print("MATCH FOUND.")
                                # --- NEW: Match_Count is length of input ---
                                found_matches.append({
                                    "Schema": s, "Table": table, 
                                    "Match_Count": len(search_data), 
                                    "Detail": search_summary
                                })
                                if show_records:
                                    print(f"    --- Matching Records (Limit {record_limit}) ---")
                                    print(df_results.to_markdown(index=False))
                                    print("    " + "-"*30)
                            else:
                                print("No match.")
                        except Exception as e:
                            print(f"Query failed ({e})")
                    else:
                        print("    [Info] Table missing one or more required columns for 'AND' search.")

                # --- 6. LOGIC FOR 'OR' MODE (HEAVILY MODIFIED) ---
                elif mode == 'OR':
                    relevant_pairs = [(c, v) for (c, v) in search_data.items() if c in table_columns]
                    if not relevant_pairs:
                        print("    [Info] No relevant columns to trace in this table.")
                        continue
                    
                    # --- NEW: Aggregation for sorting ---
                    table_match_details = []
                    
                    for col_name, value in relevant_pairs:
                        search_val_str = str(value)
                        print(f"    [Trace] {col_name}::text = '{search_val_str}'...", end=" ")
                        
                        select_clause = "*" if show_records else "1"
                        limit = record_limit if show_records else 1
                        sql = f"SELECT {select_clause} FROM {s}.{table} WHERE {col_name}::text = :val LIMIT {limit}"
                        
                        try:
                            with self.engine.connect() as conn:
                                if show_records:
                                    df_results = pd.read_sql(text(sql), conn, params={"val": search_val_str})
                                    result = not df_results.empty
                                else:
                                    result = conn.execute(text(sql), {"val": search_val_str}).fetchone()
                                    
                            if result:
                                print("MATCH FOUND.")
                                # --- NEW: Add to list for aggregation ---
                                table_match_details.append(f"{col_name} = {value}")
                                
                                if show_records:
                                    print(f"\n    --- Matching Records for this pair (Limit {record_limit}) ---")
                                    print(df_results.to_markdown(index=False))
                                    print("    " + "-"*30)
                            else:
                                print("No match.")
                        except Exception as e:
                            print(f"Query failed ({e})")
                            
                    # --- NEW: Add aggregated result to final list ---
                    if table_match_details:
                        found_matches.append({
                            "Schema": s,
                            "Table": table,
                            "Match_Count": len(table_match_details),
                            "Detail": ", ".join(table_match_details)
                        })

        # --- 7. Final Report (MODIFIED FOR SORTING) ---
        print("\n" + "="*30 + " TRACE SUMMARY " + "="*30)
        print(f"Criteria: {search_summary} (Mode: {mode})")

        if not found_matches:
            print("[RESULT] Trace complete. No matches found.")
        else:
            print("[RESULT] Trace complete. Found matches in the following tables (sorted by match count):")
            
            # --- NEW: Create DataFrame and sort by Match_Count descending ---
            df = pd.DataFrame(found_matches, columns=['Schema', 'Table', 'Match_Count', 'Detail'])
            df = df.sort_values(by='Match_Count', ascending=False)
            
            print(df.to_markdown(index=False))
            
        return found_matches

    def trace_json_origin(self, json_data: dict):
        """
        Traces the origin of a denormalized JSON object by finding all tables
        that contain the data, then analyzes the results to infer logical relationships.
        
        This is a resource-intensive operation that combines 'trace_value_across_db' 
        with an analysis layer.
        
        :param json_data: A Python dictionary (from a JSON object) representing a record.
        
        Usage:
            response_data = { "pro_id": 780, "pro_code": "300134", "total_qty": 1200, ... }
            db_tool.trace_json_origin(response_data)
        """
        print("\n[INFO] Starting JSON Origin Trace. This will take a very long time.")
        
        # --- MODIFIED: Create a dictionary (map) instead of a list ---
        search_data = {}
        for key, value in json_data.items():
            if value is not None and value != "": # Ignore null/empty values
                search_data[key] = value
        
        if not search_data:
            print("[ERROR] Input JSON is empty or contains only null values.")
            return

        # --- MODIFIED: Pass the new 'search_data' dictionary ---
        print("[INFO] Phase 1: Executing multi-pair 'OR' trace...")
        found_matches = self.trace_value_across_db(
            search_data, # Pass the dictionary here
            mode='OR', 
            scan_all_schemas=True,
            show_records=False 
        )
        
        # 3. Analyze the results
        print("\n[INFO] Phase 2: Analyzing trace results...")
        if not found_matches:
            print("[ANALYSIS] No data from the JSON was found in the database.")
            return
            
        self._analyze_trace_results(found_matches, json_data)

    def _analyze_trace_results(self, found_matches: list, json_data: dict):
        """
        Private helper method to analyze the output of a 'trace_value_across_db' run.
        
        This method aggregates matches to build two reports:
        1. Table Source Summary: Which tables supplied which keys?
        2. Logical Link Summary: Which keys appear in multiple tables,
           suggesting a logical join?
        
        :param found_matches: The list of match dictionaries from trace_value_across_db.
        :param json_data: The original input dictionary to show values for join keys.
        """
        table_key_map = defaultdict(set) # { "schema.table": {"key1", "key2"} }
        key_table_map = defaultdict(set) # { "key1": {"schema.table1", "schema.table2"} }
        
        # 1. Populate the maps
        for match in found_matches:
            full_table_name = f"{match['Schema']}.{match['Table']}"
            
            # Reconstruct the key from the 'Detail' string (e.g., "pro_id = 780")
            try:
                key = match['Detail'].split(' = ')[0].strip()
                
                table_key_map[full_table_name].add(key)
                key_table_map[key].add(full_table_name)
            except Exception:
                # Failsafe in case 'Detail' string format changes
                continue
                
        # 2. Print Table Source Summary (The "Hubs")
        print("\n" + "="*30 + " TABLE SOURCE SUMMARY " + "="*30)
        print("The following tables contributed data to the JSON object:")
        sorted_tables = sorted(table_key_map.items(), key=lambda item: len(item[1]), reverse=True)
        
        for table, keys in sorted_tables:
            print(f"\n[Table] {table} (Matched {len(keys)} keys)")
            print(f"  Contributed Keys: {', '.join(sorted(keys))}")

        # 3. Print Logical Link Summary (The "Links")
        print("\n" + "="*30 + " LOGICAL LINK ANALYSIS " + "="*30)
        print("The following keys were found in multiple tables, suggesting logical joins:")
        
        found_links = False
        sorted_keys = sorted(key_table_map.items(), key=lambda item: len(item[1]), reverse=True)
        
        for key, tables in sorted_keys:
            if len(tables) > 1:
                found_links = True
                print(f"\n[Key] '{key}' (Value: '{json_data.get(key)}')")
                print(f"  Found in {len(tables)} tables:")
                for t in sorted(tables):
                    print(f"    - {t}")
        
        if not found_links:
            print("No logical links found. Data may be from isolated tables or a single table.")

    def check_uniqueness(self, table_name, columns, schema='public'):
        """
        Checks if a specific column or combination of columns is unique within a table.
        
        It performs a 'GROUP BY' query on the specified columns. If any group has a 
        count > 1, those values are duplicates, meaning the combination is NOT unique.

        :param table_name: The table to check.
        :param columns: A list of column names to check for uniqueness together.
                        Example: ['wh_id', 'pro_id']
        :param schema: The schema where the table resides.
        
        Usage:
            db_tool.check_uniqueness('warehouse_stock', ['wh_id', 'pro_id'])
        """
        print(f"\n[INFO] Checking uniqueness for columns {columns} in '{schema}.{table_name}'...")
        
        # 1. Validate Table and Columns
        if not self.inspector.has_table(table_name, schema=schema):
            print(f"[ERROR] Table '{table_name}' does not exist in schema '{schema}'.")
            return

        try:
            existing_columns = [c['name'] for c in self.inspector.get_columns(table_name, schema=schema)]
        except Exception as e:
            print(f"[ERROR] Could not retrieve columns: {e}")
            return

        # Ensure all requested columns actually exist
        missing_cols = [col for col in columns if col not in existing_columns]
        if missing_cols:
            print(f"[ERROR] The following columns do not exist in the table: {missing_cols}")
            return

        # 2. Construct the Analysis Query
        # Logic: Group by the target columns and count occurrences. Filter for count > 1.
        cols_str = ", ".join(columns)
        sql = f"""
            SELECT {cols_str}, COUNT(*) as duplicate_count
            FROM {schema}.{table_name}
            GROUP BY {cols_str}
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 20
        """

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)

            # 3. Analyze and Report
            print("-" * 50)
            if df.empty:
                print("✅ RESULT: UNIQUE")
                print(f"The combination of {columns} is strictly unique across the table.")
                print("This combination is a valid candidate for a Primary Key.")
            else:
                print("❌ RESULT: NOT UNIQUE (Duplicates Found)")
                print(f"The combination of {columns} contains duplicates.")
                print(f"Showing top {len(df)} duplicate groups:")
                print(df.to_markdown(index=False))
                print("-" * 50)
                
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")