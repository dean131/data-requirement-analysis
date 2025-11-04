import json
import csv
import os

# --- Configuration ---
INPUT_FILENAME = 'schemas.json'
OUTPUT_FILENAME = 'data_dictionary.csv'
# ---------------------

def build_data_type_map(data):
    """
    First pass: Iterate through all columns to find embedded data type
    definitions and build a map of UUID -> type_name.
    """
    type_map = {}
    
    # Check if the main key exists
    if 'all-table-columns' not in data or len(data['all-table-columns']) < 2:
        print(f"Error: Could not find 'all-table-columns' key in {INPUT_FILENAME}.")
        return None

    try:
        columns_list = data['all-table-columns'][1]
    except (IndexError, TypeError):
        print("Error: 'all-table-columns' key does not have the expected [type, list] structure.")
        return None

    print(f"Building data type map from {len(columns_list)} column entries...")
    
    for column in columns_list:
        dtype_info = column.get('column-data-type')
        
        # Check if the data type is a full object definition
        if isinstance(dtype_info, dict):
            type_uuid = dtype_info.get('@uuid')
            type_name = dtype_info.get('name')
            
            if type_uuid and type_name and type_uuid not in type_map:
                type_map[type_uuid] = type_name
                
    print(f"Found {len(type_map)} unique data type definitions.")
    return type_map, columns_list

def process_columns(columns_list, type_map):
    """
    Second pass: Process all columns and format them for the CSV,
    using the type_map to resolve data type names.
    """
    processed_rows = []
    
    for column in columns_list:
        # Parse schema, table, and column name
        full_name = column.get('full-name', '')
        parts = full_name.split('.')
        
        schema_name = ""
        table_name = ""
        column_name = column.get('name', 'unknown_column') # Fallback

        if len(parts) == 3:
            schema_name, table_name, column_name = parts
        elif len(parts) == 2:
            table_name, column_name = parts
        
        # Get data type name
        dtype_name = "Unknown"
        dtype_info = column.get('column-data-type')
        
        if isinstance(dtype_info, dict):
            # Type is fully defined here
            dtype_name = dtype_info.get('name')
        elif isinstance(dtype_info, str):
            # Type is a UUID reference, look it up in our map
            dtype_name = type_map.get(dtype_info, "Unknown Ref")

        # Get remarks/description
        remarks = column.get('remarks', '')
        if not remarks:
            # Check the attributes map as a fallback
            remarks = column.get('attributes', {}).get('REMARKS', '')

        # Format the row as a dictionary
        row = {
            'Schema': schema_name,
            'Table': table_name,
            'Column': column_name,
            'Position': column.get('ordinal-position'),
            'Data Type': dtype_name,
            'Size': column.get('size'),
            'Nullable': 'Yes' if column.get('nullable') else 'No',
            'PK': 'Yes' if column.get('part-of-primary-key') else 'No',
            'FK': 'Yes' if column.get('part-of-foreign-key') else 'No',
            'Default': column.get('default-value') or '', # Handle None/null
            'Remarks': remarks
        }
        processed_rows.append(row)
        
    return processed_rows

def write_csv(data_rows, filename):
    """
    Writes the list of processed rows to a CSV file.
    """
    if not data_rows:
        print("No data to write. Aborting CSV creation.")
        return

    # Define the headers for the CSV file
    headers = [
        'Schema', 'Table', 'Column', 'Position', 'Data Type', 'Size', 
        'Nullable', 'PK', 'FK', 'Default', 'Remarks'
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"\nSuccess! Data dictionary written to {filename}")
    except IOError as e:
        print(f"\nError writing to file {filename}: {e}")

def main():
    """
    Main function to run the conversion process.
    """
    if not os.path.exists(INPUT_FILENAME):
        print(f"Error: Input file not found: {INPUT_FILENAME}")
        print("Please make sure 'schemas.json' is in the same directory as this script.")
        return

    print(f"Loading {INPUT_FILENAME}...")
    try:
        with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON in {INPUT_FILENAME}. {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return
        
    print("File loaded. Analyzing structure...")
    
    # Step 1: Build the data type map
    result = build_data_type_map(data)
    if not result:
        print("Could not build data type map. Exiting.")
        return
        
    type_map, columns_list = result
    
    # Step 2: Process all columns
    print("Processing all column data...")
    processed_data = process_columns(columns_list, type_map)
    
    # Step 3: Write the output CSV
    if processed_data:
        print(f"Found {len(processed_data)} columns. Writing to CSV...")
        write_csv(processed_data, OUTPUT_FILENAME)
    else:
        print("No columns were processed.")

if __name__ == "__main__":
    main()