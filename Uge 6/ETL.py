import pandas as pd
import numpy as np
from pathlib import Path
import API
import mysql.connector
from io import StringIO
import requests
import re
import polars as pl
import json

serverIP = "192.168.20.171"
local_connector = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="Velkommen25"
)

local_cursor = local_connector.cursor()
try:
    connector = mysql.connector.connect(
        host=serverIP,
        port="3306",
        user="curseist",
        password="curseword",
        connect_timeout=1
    )
    cursor = connector.cursor()
except Exception as e:
    connector = local_connector
    print("SQL failed to connect to server. Using localhost")
    cursor = local_cursor


def access_api(table):
    try:
        url = f"http://{serverIP}:8000/{table}"
        response = requests.get(url,timeout=1)
        string = json.loads(response.content.decode("utf-8"))
    except Exception as e:
        print("failed to access API. Using localhost")
        if(table == "orders"):
            string = API.read_orders()
        if(table == "customers"):
            string = API.read_customers()
        if(table == "order_items"):
            string = API.read_order_items()
    return string


def product_rename(dataframe):
    regex = r"^[a-zA-Z0-9]+ (.*) - \d{4}$"
    dataframe["product_name"] = dataframe["product_name"].str.replace(regex, r"\1",regex = True)


def sql_2_pandas(table_name):
    cursor.execute(f"USE productdb")
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
    if(len(dataframe.index.levels) == 1):
        use_auto_increment = True
    else:
        use_auto_increment = False
    
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
    print(f"added {table_name} to {database}")

    #make key autoincrement
    if(len(dataframe.index.levels)==1):
        query = f"ALTER TABLE {table_name} MODIFY {dataframe.index.names[0]} INT AUTO_INCREMENT"
        local_cursor.execute(query)
    local_connector.commit()

def convert_to_multiindex(df):
    if(type(df.index) != pd.MultiIndex):
        df.index = pd.MultiIndex.from_arrays([df.index], names=[df.index.name])

def get_data():
    tables = {}


    csv_path = Path(__file__).parent/"data"
    stores = pd.read_csv(csv_path/"stores.csv")
    staffs = pd.read_csv(csv_path/"staffs.csv")

    #bit wierd you can convert json to tables. But because the json is made from csv files it works
    orders = pd.read_json(StringIO(access_api("orders")))
    customers = pd.read_json(StringIO(access_api("customers")))
    order_items = pd.read_json(StringIO(access_api("order_items")))

    brands = sql_2_pandas("brands")
    categories = sql_2_pandas("categories")
    products = sql_2_pandas("products")
    stocks = sql_2_pandas("stocks")

    tables["stocks"] = stocks
    tables["stores"] = stores
    tables["staffs"] = staffs
    tables["orders"] = orders
    tables["customers"] = customers
    tables["order_items"] = order_items
    tables["brands"] = brands
    tables["categories"] = categories
    tables["products"] = products

    stores.index.rename("store_id", inplace = True)
    staffs.index.rename("staff_id", inplace = True)
    stores.index += 1
    staffs.index += 1

    orders.set_index("order_id", inplace = True)
    customers.set_index("customer_id", inplace = True)
    order_items.drop(["item_id"], axis = 1, inplace = True)
    order_items.set_index(["order_id","product_id"],inplace = True)

    brands.set_index("brand_id", inplace = True)
    categories.set_index("category_id", inplace = True)
    products.set_index("product_id", inplace = True)

    stores_mapping = stores["name"].to_dict()
    stores_mapping = {v:k for k,v in stores_mapping.items()}
    stocks["store_id"] = stocks["store_name"].map(stores_mapping)
    stocks.drop(["store_name"], axis = 1, inplace = True)
    stocks.set_index(["store_id", "product_id"], inplace = True)

    staffs_mapping = staffs["name"].to_dict()
    staffs_mapping = {v:k for k,v in staffs_mapping.items()}
    orders["staff_id"] = orders["staff_name"].map(staffs_mapping)
    orders.drop(["staff_name"], axis = 1, inplace = True)

    orders["store_id"] = orders["store"].map(stores_mapping)
    orders.drop(["store"], axis = 1, inplace = True)

    staffs.drop(["street"], axis = 1, inplace = True)

    staffs["store_id"] = staffs["store_name"].map(stores_mapping)
    staffs.drop(["store_name"], inplace = True, axis = 1)
    staffs["manager_id"] = staffs["manager_id"].astype('Int64')
    

    product_rename(tables["products"])


    def replace_phone_number(dataframe, column):
        def replace_function(string):
            if(string == "NULL"): return string
            return("+1"+"".join(re.findall(r'\d', string)))
        dataframe[column] = dataframe[column].map(replace_function)

    replace_phone_number(customers,"phone")
    replace_phone_number(staffs,"phone")
    replace_phone_number(stores,"phone")

    database_name = "bicycledb"
    create_database(database_name)
    for k, v in tables.items():
        convert_to_multiindex(v)
        create_table(v,k,database_name)


        pass
    def create_foreign_key(table1, table2, column_name, primary_key):
        query = f"""
            ALTER TABLE {table1} 
            ADD CONSTRAINT fk_{table1}_{column_name} 
            FOREIGN KEY ({column_name}) 
            REFERENCES {table2}({primary_key})
        """
        local_cursor.execute(query)
        
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

    
    def update_string_to_date(table, column):
        query = f"UPDATE {table} SET {column} = STR_TO_DATE({column}, '%d/%m/%Y')"
        local_cursor.execute(query)
        query = f"ALTER TABLE {table} MODIFY COLUMN {column} DATE"
        local_cursor.execute(query)


    update_string_to_date("orders", "order_date")
    update_string_to_date("orders", "required_date")
    update_string_to_date("orders", "shipped_date")
    local_connector.commit()




get_data()
local_connector.commit()
local_connector.close()
connector.close()