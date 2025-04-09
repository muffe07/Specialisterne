import pandas as pd
import numpy as np
from pathlib import Path
import API
import mysql.connector
from io import StringIO
import requests
import re
import json
import time

try:
    with open(Path(__file__).parent/"config.json") as file:
        config = json.load(file)
except FileNotFoundError as e:
    print("config file not found")
    print("you can use example_config.json to create a config.json file")
    exit()

last_time = time.time()
def get_time_diff():
    global last_time
    now = time.time()
    diff = now - last_time
    last_time = now
    return diff

#serverIP = "192.168.20.171"
local_connector = mysql.connector.connect(
    host="localhost",
    port="3306",
    user=config["local_SQL_user"],
    password=config["local_SQL_password"]
)
print(f"local_host_connection: {get_time_diff():.2f}s")

local_cursor = local_connector.cursor()
try:
    connector = mysql.connector.connect(
        host=config["remote_IP"],
        port="3306",
        user=config["remote_SQL_user"],
        password=config["remote_SQL_password"],
        connect_timeout=1
    )
    cursor = connector.cursor()
except Exception as e:
    connector = local_connector
    print("SQL failed to connect to server. Using localhost")
    cursor = local_cursor
print(f"remote_SQL_connection: {get_time_diff():.2f}s")


def access_api(table):
    try:
        url = f"http://{config["remote_IP"]}:8000/{table}"
        response = requests.get(url,timeout=1)
        string = json.loads(response.content.decode("utf-8"))
    except Exception as e:
        print("failed to access API. Using localhost")
        match table:
            case "orders":
                string = API.read_orders()
            case "customers":
                string = API.read_customers()
            case "order_items":
                string = API.read_order_items()
            case _:
                print("failed to find table using local API")
                print("exiting")
                exit()
    return string

def sql_to_pandas(table_name):
    cursor.execute(f"USE {config["remote_database_name"]}")
    cursor.execute(f"DESCRIBE {table_name}")
    header = np.array(cursor.fetchall())
    cursor.execute(f"select * from {table_name}")
    dataframe = pd.DataFrame(cursor.fetchall(),columns = header[:,0])
    return dataframe

def create_database(name):
    local_cursor.execute(f"DROP DATABASE IF EXISTS {name}")
    local_cursor.execute(f"CREATE DATABASE {name}")
    local_connector.commit()

def create_table(dataframe, table_name, database):
    #setup
    local_cursor.execute(f"USE {database}")
    local_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    #create table and header
    column_dtypes = pd.concat([dataframe.index.dtypes, dataframe.dtypes])
    
    key = ", ".join([str(k) for k,v in dataframe.index.dtypes.items()])
    dtype_dict = {"int64":"int", "Int64":"int", "object":"varchar(255)","float64":"decimal(16,2)"}
    column_header = ",\n".join([f"{k} {dtype_dict[str(v)]}" for k,v in column_dtypes.items()])

    query = (f"""CREATE TABLE {table_name} (\n{column_header},\nPRIMARY KEY ({key})\n)""")
    local_cursor.execute(query)

    #insert data
    data_substitude = ", ".join(["%s"]*len(column_dtypes))
    query = f"INSERT INTO {table_name} ({", ".join(column_dtypes.keys())}) VALUES ({data_substitude})"
    data = dataframe.reset_index().replace({np.nan:None,"NULL":None}).to_numpy().tolist()
    local_cursor.executemany(query,data)
    #print(f"added {table_name} to {database}")

    #make key autoincrement
    if(len(dataframe.index.levels)==1):
        query = f"ALTER TABLE {table_name} MODIFY {dataframe.index.names[0]} INT AUTO_INCREMENT"
        local_cursor.execute(query)
    local_connector.commit()

def convert_to_multiindex(df):
    if(type(df.index) != pd.MultiIndex):
        df.index = pd.MultiIndex.from_arrays([df.index], names=[df.index.name])

def product_rename(dataframe):
    regex = r"^[a-zA-Z0-9]+ (.*) - \d{4}$"
    dataframe["product_name"] = dataframe["product_name"].str.replace(regex, r"\1",regex = True)

def replace_phone_number(dataframe, column):
    def replace_function(string):
        if(string == "NULL"): return string
        return("+1"+"".join(re.findall(r'\d', string)))
    dataframe[column] = dataframe[column].map(replace_function)

def create_foreign_key(table1, table2, column_name, primary_key):
    query = f"""
        ALTER TABLE {table1} 
        ADD CONSTRAINT fk_{table1}_{column_name} 
        FOREIGN KEY ({column_name}) 
        REFERENCES {table2}({primary_key})
    """
    local_cursor.execute(query)
    
def update_string_to_date(table, column):
    query = f"UPDATE {table} SET {column} = STR_TO_DATE({column}, '%d/%m/%Y')"
    local_cursor.execute(query)
    query = f"ALTER TABLE {table} MODIFY COLUMN {column} DATE"
    local_cursor.execute(query)

def get_data():
    csv_path = Path(__file__).parent/"data"
    stores = pd.read_csv(csv_path/"stores.csv")
    staffs = pd.read_csv(csv_path/"staffs.csv")

    #bit wierd you can convert json to tables. But because the json is made from csv files it works
    orders = pd.read_json(StringIO(access_api("orders")))
    customers = pd.read_json(StringIO(access_api("customers")))
    order_items = pd.read_json(StringIO(access_api("order_items")))

    brands = sql_to_pandas("brands")
    categories = sql_to_pandas("categories")
    products = sql_to_pandas("products")
    stocks = sql_to_pandas("stocks")

    print(customers)
    exit()
    tables = {}
    tables["stocks"] = stocks
    tables["stores"] = stores
    tables["staffs"] = staffs
    tables["orders"] = orders
    tables["customers"] = customers
    tables["order_items"] = order_items
    tables["brands"] = brands
    tables["categories"] = categories
    tables["products"] = products
    return(tables)

#renames all dataframe indexes to correct table key (multiindex in case of composite key)
def key_restructuring(tables):
    #rename index to key
    tables["stores"].index.rename("store_id", inplace = True)
    tables["staffs"].index.rename("staff_id", inplace = True)

    tables["orders"].set_index("order_id", inplace = True)
    tables["customers"].set_index("customer_id", inplace = True)

    tables["brands"].set_index("brand_id", inplace = True)
    tables["categories"].set_index("category_id", inplace = True)
    tables["products"].set_index("product_id", inplace = True)

    #change to 1 indexing
    tables["stores"].index += 1
    tables["staffs"].index += 1

    #change rename forgein keys to use id instead of name
    #store id
    stores_mapping = tables["stores"]["name"].to_dict()
    stores_mapping = {v:k for k,v in stores_mapping.items()}
    tables["stocks"]["store_id"] = tables["stocks"]["store_name"].map(stores_mapping)
    tables["stocks"].drop(["store_name"], axis = 1, inplace = True)

    tables["orders"]["store_id"] = tables["orders"]["store"].map(stores_mapping)
    tables["orders"].drop(["store"], axis = 1, inplace = True)

    tables["staffs"]["store_id"] = tables["staffs"]["store_name"].map(stores_mapping)
    tables["staffs"].drop(["store_name"], inplace = True, axis = 1)

    #staff id
    staffs_mapping = tables["staffs"]["name"].to_dict()
    staffs_mapping = {v:k for k,v in staffs_mapping.items()}
    tables["orders"]["staff_id"] = tables["orders"]["staff_name"].map(staffs_mapping)
    tables["orders"].drop(["staff_name"], axis = 1, inplace = True)

    #set multiindex after renamed foreign keys
    tables["order_items"].set_index(["order_id","product_id"],inplace = True) 
    tables["stocks"].set_index(["store_id", "product_id"], inplace = True) 

    #drop other unnecessary columns
    #equal to stores["street"]
    tables["staffs"].drop(["street"], axis = 1, inplace = True) 

    #not needed as order_id and product_id works as a key
    tables["order_items"].drop(["item_id"], axis = 1, inplace = True)
    
    
def create_schema(tables):
    database_name = config["local_database_name"]
    create_database(database_name)
    for k, v in tables.items():
        convert_to_multiindex(v)
        create_table(v,k,database_name)

def data_standardization_before_creation(tables):
    #change from int64 to Int64 to handle null values better
    tables["staffs"]["manager_id"] = tables["staffs"]["manager_id"].astype('Int64')

    product_rename(tables["products"])

    replace_phone_number(tables["customers"],"phone")
    replace_phone_number(tables["staffs"],"phone")
    replace_phone_number(tables["stores"],"phone")

def data_standadization_after_creation():
    #foreign key requires both tables to exist
    create_foreign_key("products", "categories", "category_id", "category_id")
    create_foreign_key("products", "brands", "brand_id", "brand_id")
    create_foreign_key("orders", "customers", "customer_id", "customer_id")
    create_foreign_key("orders", "staffs", "staff_id", "staff_id")
    create_foreign_key("staffs", "staffs", "manager_id", "staff_id")
    create_foreign_key("staffs", "stores", "store_id", "store_id")
    create_foreign_key("stocks", "products", "product_id", "product_id")
    create_foreign_key("stocks", "stores", "store_id", "store_id")
    create_foreign_key("order_items", "orders", "order_id", "order_id")
    create_foreign_key("order_items", "products", "product_id", "product_id")
    create_foreign_key("orders", "stores", "store_id", "store_id")
    print(f"foreign keys added: {get_time_diff():.2f}s")

    #pandas does not support dates without time therefore dtype is changed after creation in SQL
    update_string_to_date("orders", "order_date")
    update_string_to_date("orders", "required_date")
    update_string_to_date("orders", "shipped_date")


if __name__ == "__main__":
    tables = get_data()
    print(f"data retrived: {get_time_diff():.2f}s")
    key_restructuring(tables)
    print(f"keys restructered: {get_time_diff():.2f}s")
    data_standardization_before_creation(tables)
    print(f"data standardized1: {get_time_diff():.2f}s")
    create_schema(tables)
    print(f"schema created: {get_time_diff():.2f}s")
    data_standadization_after_creation()
    print(f"data standardized2: {get_time_diff():.2f}s")

    local_connector.commit()
    local_connector.close()
    #connector does not need to commit as there should be no changes to source database
    connector.close()