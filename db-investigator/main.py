from dotenv import load_dotenv
load_dotenv()
import os
from db_investigator import (
    DBTool
)

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

# Initialize the tool using the loaded config
try:
    db_tool = DBTool(**db_config)

    # Run the commands here

    db_tool.show_features()
    # db_tool.list_tables(list_all_schemas=True)
    # db_tool.search_metadata("cust_id")

    data = {
        "wh_id" : 254,
        "pro_id": 780,
        "pro_code": "300134",
        "pro_name": "VAPE ONE PUSH GREE TEA 30 HRI  ",
        "qty1": 0,
        "qty2": 0,
        "qty3": 100,
        "unit_id1": "PCS",
        "unit_id2": "KRT",
        "unit_id3": "KRT",
    }

    # data = [
    #     ('wh_id', '254'),
    #     ('pro_id', '780'),
    # ]
    # db_tool.trace_value_across_db(data, mode='AND', scan_all_schemas=True, show_records=True)

    # data = {
    #     "pro_id": 780,
    #     "pro_code": "300134",
    #     "pro_name": "VAPE ONE PUSH GREE TEA 30 HRI  ",
    #     "unit_id1": "PCS",
    #     "unit_id2": "KRT",
    #     "unit_id3": "KRT",
    #     "purch_price1": 20182,
    #     "purch_price2": 242184,
    #     "purch_price3": 242184,
    #     "sell_price1": 20182,
    #     "sell_price2": 242184,
    #     "sell_price3": 242184,
    #     "total_qty": 1200,
    #     "qty1": 0,
    #     "qty2": 0,
    #     "qty3": 100,
    #     "total_qty_order": 0,
    #     "qty_order1": 0,
    #     "qty_order2": 0,
    #     "qty_order3": 0,
    #     "total_qty_inc_on_order": 0,
    #     "qty_inc_on_order1": 0,
    #     "qty_inc_on_order2": 0,
    #     "qty_inc_on_order3": 100,
    #     "conv_unit2": 12,
    #     "conv_unit3": 1,
    #     "is_active": True,
    #     "vat": 11,
    #     "vat_lg_purch": 0,
    #     "vat_lg_sell": 0
    # }

    # db_tool.list_tables(list_all_schemas=True)
    # db_tool.get_table_details('m_product', 'mst')
    # db_tool.trace_value_across_db(data, mode = 'OR', scan_all_schemas = True, show_records = True)
    # db_tool.trace_json_origin(data)

except Exception as e:
    print(f"[ERROR] Failed to initialize DBTool. Check credentials: {e}")