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
    
    def trace_value_across_db(self, column_name, value, schema='public', scan_all_schemas=False):
        """
        Traces a specific value in a specific column across tables.
        
        Can operate in two modes:
        1. Single Schema (default): Scans all tables in the specified 'schema'.
        2. All Schemas: If 'scan_all_schemas' is True, it ignores the 'schema' 
           parameter and scans all tables in all discoverable schemas.
        
        :param column_name: The name of the column to search for (e.g., 'vat').
        :param value: The exact value to match (e.g., 11 or 'some-uuid').
        :param schema: The schema to scan (ignored if 'scan_all_schemas' is True).
        :param scan_all_schemas: Flag to enable scanning all schemas.
        
        Usage (Default Schema): db_tool.trace_value_across_db("user_id", 123)
        Usage (All Schemas):    db_tool.trace_value_across_db("user_id", 123, scan_all_schemas=True)
        """
        print(f"\n[INFO] Tracing value '{value}' in column '{column_name}'...")
        
        found_matches = [] # Will store results as dictionaries {Schema, Table}
        search_val_str = str(value)

        # 1. Determine which schemas to scan
        if scan_all_schemas:
            print("[INFO] Mode: Scanning ALL schemas.")
            try:
                target_schemas = self.inspector.get_schema_names()
            except Exception as e:
                print(f"[ERROR] Could not retrieve schema list: {e}")
                return []
        else:
            print(f"[INFO] Mode: Scanning single schema: '{schema}'.")
            target_schemas = [schema]

        # 2. Outer loop: Iterate through each target schema
        for s in target_schemas:
            print(f"\n--- Scanning Schema: {s} ---")
            try:
                all_tables = self.inspector.get_table_names(schema=s)
            except Exception as e:
                # This can happen for protected system schemas
                print(f"  [WARN] Could not access or list tables in schema '{s}', skipping: {e}")
                continue

            if not all_tables:
                print("  [INFO] No tables found in this schema.")
                continue

            # 3. Inner loop: Iterate through tables in the current schema
            for table in all_tables:
                print(f"  [Scan] Checking table: {table}...", end=" ")
                
                # Optimization 1: Check if the column exists
                try:
                    table_columns = [c['name'] for c in self.inspector.get_columns(table, schema=s)]
                except Exception as e:
                    print(f"Failed to inspect columns ({e})")
                    continue # Skip this table

                if column_name not in table_columns:
                    print("Column not found.")
                    continue

                # Optimization 2: Column exists, check for the value
                sql = f"SELECT 1 FROM {s}.{table} WHERE {column_name}::text = :val LIMIT 1"
                
                try:
                    with self.engine.connect() as conn:
                        result = conn.execute(text(sql), {"val": search_val_str}).fetchone()
                    
                    if result:
                        print("MATCH FOUND.")
                        found_matches.append({"Schema": s, "Table": table})
                    else:
                        print("No match.")
                except Exception as e:
                    # This may fail if a column is a complex type (e.g., array, jsonb)
                    print(f"Query failed ({e})")

        # 4. Final Report
        if not found_matches:
            print("\n[RESULT] Trace complete. No matches found.")
        else:
            print("\n[RESULT] Trace complete. Found matches in the following tables:")
            df = pd.DataFrame(found_matches)
            print(df.to_markdown(index=False))
            
        return found_matches
    

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

    except Exception as e:
        print(f"[ERROR] Failed to initialize DBTool. Check credentials: {e}")