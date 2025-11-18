import pandas as pd
import inspect
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect as sqlalchemy_inspect, text
from sqlalchemy.exc import SQLAlchemyError

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

    def search_table(self, table_name, search_term):
        """
        Searches for a specific term within all text-compatible columns of a given table.
        
        This method uses column introspection to filter out non-text columns (like INTEGER or DATE),
        preventing SQL type mismatch errors during the search.
        
        :param table_name: The name of the table to search.
        :param search_term: The string value to search for.
        
        Usage: db_tool.search_table("users", "admin_user")
        """
        print(f"\n[INFO] Searching table '{table_name}' for: '{search_term}'...")

        # Validate table existence to prevent runtime errors or invalid SQL generation
        if not self.inspector.has_table(table_name):
            print(f"[ERROR] Table '{table_name}' does not exist in the database.")
            return

        # Retrieve column metadata to identify text-based columns.
        columns = self.inspector.get_columns(table_name)
        text_columns = [
            col['name'] for col in columns 
            if str(col['type']).startswith(('VARCHAR', 'TEXT', 'CHAR', 'UUID'))
        ]

        if not text_columns:
            print("[WARN] No text-compatible columns found in this table. Aborting search.")
            return

        # Construct a dynamic SQL query.
        conditions = [f"{col}::text ILIKE :term" for col in text_columns]
        sql_query = f"SELECT * FROM {table_name} WHERE " + " OR ".join(conditions)

        try:
            # Execute the query using a parameterized approach to prevent SQL injection.
            with self.engine.connect() as conn:
                df = pd.read_sql(text(sql_query), conn, params={"term": f"%{search_term}%"})
            
            # Display results using Pandas for readability
            if df.empty:
                print("[RESULT] No matches found.")
            else:
                print(f"[RESULT] Found {len(df)} matches:")
                print(df.to_markdown(index=False))
                
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")

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

    def search_metadata(self, search_term):
        """
        Searches the database schema (not the data) to find tables or columns 
        matching the search term. 
        
        Useful for locating where specific data concepts (like 'email' or 'order_id') 
        exist structurally in the database.
        
        Usage: db_tool.search_metadata("user_id")
        """
        print(f"\n[INFO] Searching schema for term: '{search_term}'...")
        
        matches = []
        # Note: This scans all tables regardless of schema by default
        all_tables = self.inspector.get_table_names() 

        for table in all_tables:
            # Check if table name matches
            if search_term.lower() in table.lower():
                matches.append({"Type": "Table", "Name": table, "Detail": "Table Name Match"})

            # Check columns within the table
            columns = self.inspector.get_columns(table)
            for col in columns:
                if search_term.lower() in col['name'].lower():
                    matches.append({
                        "Type": "Column", 
                        "Name": table, 
                        "Detail": f"Column: {col['name']}"
                    })

        if matches:
            df = pd.DataFrame(matches)
            print(df.to_markdown(index=False))
        else:
            print("[RESULT] No schema matches found.")
    
    def trace_value_across_db(self, search_pairs: list, mode='OR', schema='public', 
                              scan_all_schemas=False, show_records=False, record_limit=5):
        """
        Traces one or more (column, value) pairs across tables with 'AND' or 'OR' logic.
        
        Can optionally display the actual matching records from the database.
        
        :param search_pairs: A list of (column, value) tuples. 
                             Example: [('user_id', 123), ('email', 'test@example.com')]
        :param mode: 'OR' (default) - Finds tables matching ANY pair.
                     'AND' - Finds tables where a SINGLE ROW matches ALL pairs.
        :param schema: The schema to scan (ignored if 'scan_all_schemas' is True).
        :param scan_all_schemas: Flag to enable scanning all schemas.
        :param show_records: (Optional) If True, displays the first 'record_limit' matching rows.
        :param record_limit: (Optional) Sets the number of records to display (default: 5).
        
        Usage (AND mode, Show Records): 
            pairs = [('wh_id', 254), ('pro_id', 780)]
            db_tool.trace_value_across_db(pairs, mode='AND', scan_all_schemas=True, show_records=True)
        Usage (OR mode, Show 10 Records):
            db_tool.trace_value_across_db(pairs, show_records=True, record_limit=10)
        """
        # --- 1. Input Validation ---
        mode = mode.upper()
        if mode not in ('AND', 'OR'):
            print(f"\n[ERROR] Invalid mode '{mode}'. Must be 'AND' or 'OR'.")
            return []
        # (Other validation remains...)
        
        search_summary = " AND ".join([f"({c} = {v})" for c, v in search_pairs]) if mode == 'AND' else " OR ".join([f"({c} = {v})" for c, v in search_pairs])
        print(f"\n[INFO] Tracing for pairs with mode: {mode}")
        if mode == 'AND':
            print(f"  Looking for: {search_summary}")

        found_matches = [] 
        
        # --- 2. Determine Schemas (No changes here) ---
        if scan_all_schemas:
            # (schema discovery logic)
            print("[INFO] Scanning ALL schemas.")
            try:
                target_schemas = self.inspector.get_schema_names()
            except Exception as e:
                print(f"[ERROR] Could not retrieve schema list: {e}")
                return []
        else:
            print(f"[INFO] Scanning single schema: '{schema}'.")
            target_schemas = [schema]

        # --- 3. Outer Schema Loop (No changes here) ---
        for s in target_schemas:
            # (schema iteration logic)
            print(f"\n--- Scanning Schema: {s} ---")
            try:
                all_tables = self.inspector.get_table_names(schema=s)
            except Exception as e:
                print(f"  [WARN] Could not access or list tables in schema '{s}', skipping: {e}")
                continue
            if not all_tables:
                print("  [INFO] No tables found in this schema.")
                continue

            # --- 4. Inner Table Loop (No changes here) ---
            for table in all_tables:
                # (table iteration logic)
                print(f"  [Scan] Checking table: {table}...")
                try:
                    table_columns = [c['name'] for c in self.inspector.get_columns(table, schema=s)]
                except Exception as e:
                    print(f"    [WARN] Failed to inspect columns ({e}), skipping table.")
                    continue 
                
                # --- 5. LOGIC FOR 'AND' MODE (MODIFIED) ---
                if mode == 'AND':
                    required_cols = [p[0] for p in search_pairs]
                    if all(col in table_columns for col in required_cols):
                        conditions = []
                        params = {}
                        for i, (col, val) in enumerate(search_pairs):
                            param_name = f"val{i}"
                            conditions.append(f"{col}::text = :{param_name}")
                            params[param_name] = str(val)
                        
                        sql_conditions = " AND ".join(conditions)
                        
                        # --- NEW: Dynamic SQL for query ---
                        select_clause = "*" if show_records else "1"
                        limit = record_limit if show_records else 1
                        sql = f"SELECT {select_clause} FROM {s}.{table} WHERE {sql_conditions} LIMIT {limit}"

                        print(f"    [Trace] Checking for '{search_summary}'...", end=" ")
                        try:
                            with self.engine.connect() as conn:
                                # --- NEW: Use read_sql for 'show_records', else use fast 'execute' ---
                                if show_records:
                                    df_results = pd.read_sql(text(sql), conn, params=params)
                                    result = not df_results.empty
                                else:
                                    result = conn.execute(text(sql), params).fetchone()
                            
                            if result:
                                print("MATCH FOUND.")
                                found_matches.append({
                                    "Schema": s, "Table": table, 
                                    "Match_Type": "AND", "Detail": search_summary
                                })
                                # --- NEW: Display records if requested ---
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

                # --- 6. LOGIC FOR 'OR' MODE (MODIFIED) ---
                elif mode == 'OR':
                    relevant_pairs = [(c, v) for (c, v) in search_pairs if c in table_columns]
                    if not relevant_pairs:
                        print("    [Info] No relevant columns to trace in this table.")
                        continue
                    
                    for col_name, value in relevant_pairs:
                        search_val_str = str(value)
                        print(f"    [Trace] {col_name}::text = '{search_val_str}'...", end=" ")
                        
                        # --- NEW: Dynamic SQL for query ---
                        select_clause = "*" if show_records else "1"
                        limit = record_limit if show_records else 1
                        sql = f"SELECT {select_clause} FROM {s}.{table} WHERE {col_name}::text = :val LIMIT {limit}"
                        
                        try:
                            with self.engine.connect() as conn:
                                # --- NEW: Use read_sql for 'show_records', else use fast 'execute' ---
                                if show_records:
                                    df_results = pd.read_sql(text(sql), conn, params={"val": search_val_str})
                                    result = not df_results.empty
                                else:
                                    result = conn.execute(text(sql), {"val": search_val_str}).fetchone()
                                    
                            if result:
                                print("MATCH FOUND.")
                                found_matches.append({
                                    "Schema": s, "Table": table, 
                                    "Match_Type": "OR", "Detail": f"{col_name} = {value}"
                                })
                                # --- NEW: Display records if requested ---
                                if show_records:
                                    print(f"\n    --- Matching Records (Limit {record_limit}) ---")
                                    print(df_results.to_markdown(index=False))
                                    print("    " + "-"*30)
                            else:
                                print("No match.")
                        except Exception as e:
                            print(f"Query failed ({e})")

        # --- 7. Final Report (MODIFIED) ---
        print("\n" + "="*30 + " TRACE SUMMARY " + "="*30)
        print(f"Criteria: {search_summary} (Mode: {mode})")

        if not found_matches:
            print("[RESULT] Trace complete. No matches found.")
        else:
            print("[RESULT] Trace complete. Found matches in the following tables:")
            df = pd.DataFrame(found_matches, columns=['Schema', 'Table', 'Match_Type', 'Detail'])
            df = df.sort_values(by=['Schema', 'Table'])
            print(df.to_markdown(index=False))
            
        return found_matches
    
    def _build_schema_cache(self, force_refresh=False):
        """
        Scans the entire database to build a cache of all tables and their 
        primary key (PK) columns.
        
        This is a performance optimization for relationship mapping.
        
        :param force_refresh: If True, rebuilds the cache.
        """
        # Check if cache already exists
        if hasattr(self, '_pk_map') and not force_refresh:
            return # Cache is already built

        print("[INFO] Building schema cache... (This may take a moment)")
        self._pk_map = {} # Stores {'schema.table': 'pk_column_name'}
        
        try:
            schemas = self.inspector.get_schema_names()
        except Exception as e:
            print(f"[ERROR] Could not retrieve schemas: {e}")
            return

        for s in schemas:
            try:
                tables = self.inspector.get_table_names(schema=s)
            except Exception:
                continue # Skip inaccessible schemas
            
            for t in tables:
                key = f"{s}.{t}"
                try:
                    pk_info = self.inspector.get_pk_constraint(t, schema=s)
                    if pk_info and pk_info.get('constrained_columns'):
                        # Store the first column of the PK
                        self._pk_map[key] = pk_info['constrained_columns'][0]
                except Exception:
                    continue # Skip tables we can't inspect
        
        print(f"[INFO] Cache built. Found {len(self._pk_map)} tables with Primary Keys.")

    def map_logical_relationships(self, input_data: dict, deep_trace=False):
        """
        Analyzes a dictionary (from JSON) to infer logical database relationships.
        
        It uses two methods:
        1. Naming Convention (Fast): Matches 'xxx_id' keys to table PKs.
        2. Value Tracing (Slow): Uses 'trace_value_across_db' to find where the data lives.
        
        :param input_data: The flat dictionary of data to analyze.
        :param deep_trace: If True, enables the slow Value Tracing heuristic.
        
        Usage:
            data = {'pro_id': 780, 'unit_id1': 'PCS', 'pro_name': 'VAPE'}
            db_tool.map_logical_relationships(data, deep_trace=True)
        """
        # 1. Ensure the schema cache is built
        self._build_schema_cache()
        if not hasattr(self, '_pk_map'):
            print("[ERROR] Schema cache is empty. Cannot map relationships.")
            return

        print(f"\n[INFO] Mapping logical relationships for {len(input_data)} keys...")
        
        inferred_links = []

        # 2. Heuristic 1: Naming Convention (Fast Scan)
        print("[INFO] Running Heuristic 1: Naming Convention...")
        for key in input_data.keys():
            if not key.endswith(('_id', '_code')):
                continue # Only check keys that look like identifiers

            base_name = key.replace('_id', '').replace('_code', '') # e.g., 'pro', 'unit'
            
            # Generate plural/singular candidate table names
            candidates = [
                base_name,
                base_name + 's',
                base_name + 'es'
            ]
            
            # Check candidates against our PK map cache
            for table_key, pk_col in self._pk_map.items():
                schema, table = table_key.split('.')
                
                if table in candidates:
                    inferred_links.append({
                        "Input_Key": key,
                        "Heuristic": "Naming",
                        "Confidence": "Medium",
                        "Inferred_Table": table_key,
                        "Detail": f"Input key '{key}' matches table '{table_key}' (PK: {pk_col})"
                    })

        # 3. Heuristic 2: Value Tracing (Deep Scan)
        if deep_trace:
            print("\n[INFO] Running Heuristic 2: Deep Value Tracing... (This will be slow)")
            
            # We will trace for two patterns:
            # 1. `id` == value (for PKs)
            # 2. `key` == value (for the key itself)
            
            search_pairs = []
            for key, value in input_data.items():
                # Only trace non-trivial values
                if value is None or (isinstance(value, str) and not value):
                    continue
                
                # Search for tables where 'id' == value
                search_pairs.append(('id', value))
                # Search for tables where the column has the same name as the key
                search_pairs.append((key, value))

            # Use our existing trace function!
            # We only care about the unique tables, so we process the results
            trace_results = self.trace_value_across_db(search_pairs, mode='OR', scan_all_schemas=True)
            
            # Process trace results to enhance our map
            for match in trace_results:
                inferred_links.append({
                    "Input_Key": f"~{match['Column']}", # Use ~ to show it's from tracing
                    "Heuristic": "Value Trace",
                    "Confidence": "High",
                    "Inferred_Table": f"{match['Schema']}.{match['Table']}",
                    "Detail": f"Found value '{match['Value_Found']}' in column '{match['Column']}'"
                })

        # 4. Final Report
        if not inferred_links:
            print("\n[RESULT] No logical relationships could be inferred.")
            return

        print("\n[RESULT] Inferred Relationship Map:")
        df = pd.DataFrame(inferred_links)
        
        # Clean up and de-duplicate the report
        df = df.drop_duplicates()
        df = df.sort_values(by=['Confidence', 'Inferred_Table'])
        print(df.to_markdown(index=False))
    

# --- Execution Entry Point ---
if __name__ == "__main__":
    
    # 1. Load variables from the .env file into the environment
    load_dotenv()

    # 2. Read the credentials from the environment using os.getenv()
    db_config = {
        "username": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME")
    }
    
    # Simple check to ensure all variables were loaded
    if not all(db_config.values()):
        print("[ERROR] One or more database configuration variables are missing.")
        print("[INFO] Please check your .env file.")
        exit()

    # 3. Initialize the tool using the loaded config
    try:
        db_tool = DBTool(**db_config)
        
        # 4. Run the commands here
        db_tool.show_features()
        # db_tool.list_tables(list_all_schemas=True)
        # db_tool.search_metadata("cust_id")

# "wh_id :   254
# "pro_id": 780,
# "pro_code": "300134",
# "pro_name": "VAPE ONE PUSH GREE TEA 30 HRI  ",
# "qty1": 0,
# "qty2": 0,
# "qty3": 100,
# "unit_id1": "PCS",
# "unit_id2": "KRT",
# "unit_id3": "KRT",

        # data = [
        #     ('wh_id', '254'),
        #     ('pro_id', '780'),
        # ]
        # db_tool.trace_value_across_db(data, mode='AND', scan_all_schemas=True, show_records=True)

        data = {
            "pro_id": 780,
            "pro_code": "300134",
            "pro_name": "VAPE ONE PUSH GREE TEA 30 HRI  ",
            "unit_id1": "PCS",
            "unit_id2": "KRT",
            "unit_id3": "KRT",
            "purch_price1": 20182,
            "purch_price2": 242184,
            "purch_price3": 242184,
            "sell_price1": 20182,
            "sell_price2": 242184,
            "sell_price3": 242184,
            "total_qty": 1200,
            "qty1": 0,
            "qty2": 0,
            "qty3": 100,
            "total_qty_order": 0,
            "qty_order1": 0,
            "qty_order2": 0,
            "qty_order3": 0,
            "total_qty_inc_on_order": 0,
            "qty_inc_on_order1": 0,
            "qty_inc_on_order2": 0,
            "qty_inc_on_order3": 100,
            "conv_unit2": 12,
            "conv_unit3": 1,
            "is_active": True,
            "vat": 11,
            "vat_lg_purch": 0,
            "vat_lg_sell": 0
        }
        db_tool.map_logical_relationships(data, deep_trace=True)

    except Exception as e:
        print(f"[ERROR] Failed to initialize DBTool. Check credentials: {e}")